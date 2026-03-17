import asyncio
import contextlib
import json
import logging
import uuid
from typing import TypedDict, List
from sqlalchemy import text

import gradio
from langchain.agents import create_agent
from langchain.agents.middleware.types import _InputAgentState
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, RemoveMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.constants import START, END
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langgraph.typing import ContextT, StateT, InputT, OutputT

from ResumeAnalyse import utils
from ResumeAnalyse.constants import get_resume_analysis_redis_key, CONVERSATION_MAX_DIALOGUES, CONVERSATION_MAX_TOKENS, \
    RESUME_ANALYSIS_REDIS_TTL, RESUME_ANALYSIS_CUCKOO_FILTER_REDIS_KEY, NULL_REDIS_TTL
from ResumeAnalyse.entity.state import ConversationState
from ResumeAnalyse.entity.thread_local import thread_resume_summary_text, thread_job_hunting_advice, \
    thread_jd_summary_text, thread_match_score, \
    thread_resume_advice
from ResumeAnalyse.utils import redis_client, mysql_engine
from ResumeAnalyse.entity.mcp import tongyi_web_search_mcp_config, amap_maps_mcp_config, tongyi_web_parser, \
    jina_web_search_mcp_config, mcp_list

Model_Name = "openrouter/free"
Base_URL = "https://openrouter.ai/api/v1"
conversation_llm = init_chat_model(
    model=Model_Name,
    base_url=Base_URL,
    model_provider="openai",
    api_key=utils.openrouter_api_key,
)

# 对话智能体的系统提示词
conversation_system_prompt_template = PromptTemplate.from_template(template=
"""你是一个专业的求职助手，能够帮助用户分析简历和职位描述，提供有价值的建议和指导。
如果用户的身份是“求职者”，请从求职者的角度回答用户的简历与目标岗位的相关问题；
如果用户的身份是“招聘者”，请从招聘者的角度回答用户对于当前这位候选人的简历与招聘岗位的相关问题。
如果用户的身份是“未知”，你可以先尝试询问用户的身份信息，以便更好地提供帮助。

以下是你需要记住的重要信息：

###
1. 用户的身份：{user_role}

2. 用户提供的简历内容概述如下：
{resume_summary_text}

3. 用户提供的职位描述内容概述如下：
{jd_summary_text}
###

4. 用户经过智能简历分析系统，目前得到的分析结果如下：
简历与职位描述的匹配度分数（百分制。如果是-1或其他负数值，则表示分数无效！）：{match_score}
简历与职位描述的差异点（如果为空，请忽略该字段）：{differences}
简历改进建议（如果为空，请忽略该字段）：{resume_advice}
求职建议（如果为空，请忽略该字段）：{job_hunting_advice}
**注意事项：以上出现值为空或者无效的字段的话，这类字段就不具有参考必要，你应当忽略或告知用户你获取到了无效的信息！并在需要时，尝试从对话历史（如果有的话）中获取相关信息！**

5. 请注意你拥有以下工具：
(1) 网络搜索工具：可以帮助你获取最新的新闻、信息和数据，特别是在你遇到不熟悉的领域或者不确定的问题时，可以通过调用网络搜索工具来获取最新的信息，并以此辅助你更好地回答用户的问题。
(2) 地图工具：可以帮助你查询地理位置、路径规划、天气查询等信息。
(3) 网页解析工具：可以帮助你从网页中提取有用的信息。
你需要根据用户的请求，智能地判断是否需要调用工具，应该调用哪个或哪些工具。
例如：
用户的请求为“请帮我搜索一下最近的科技新闻”，你应该调用网络搜索工具来完成任务。
用户的请求为“请帮我查看https://www.google.com/这个网页，并告诉我这个网页的内容”，你应该调用网页解析工具来完成任务。
...
记住：如果调用了工具，将工具返回的信息加以思考和整理之后再反馈给用户。
"""
)

mcp_clients = []    # 全局共享的、成功初始化的MCP客户端列表
mcp_status = {}     # 全局共享的MCP客户端状态字典


def init_mcp_clients():
    """
    初始化多个MCP客户端实例，并将它们存入全局列表 mcp_clients 中。
    """
    clients = []
    status = {}
    for mcp_name in mcp_list:
        try:
            client = MultiServerMCPClient(
                {
                    mcp_name: mcp_list[mcp_name]
                }
            )
            clients.append(client)
            status[mcp_name] = "running"
            logging.info(f"MCP客户端 {mcp_name} 初始化成功。")
        except Exception as e:
            logging.error(f"MCP客户端 {mcp_name} 初始化失败: {e}")
            logging.info(f"智能体将暂时无法使用该MCP工具: {mcp_name}")
            status[mcp_name] = "failed"

    return clients, status


# 初始化MCP客户端
mcp_clients, mcp_status = init_mcp_clients()
# 全局共享的MCP工具列表，用于初始化多个agent
global_mcp_tools = None
# 异步获取MCP工具的任务句柄，避免重复创建任务
get_tools_task = None
# 全局初始化锁，确保并发安全
init_lock = asyncio.Lock()


class SessionContext(TypedDict):
    conversation_agent: CompiledStateGraph[TypedDict, ContextT, _InputAgentState, TypedDict]
    conversation_config: dict


"""
登记当前会话的上下文信息。目前每个会话需要记录的信息如下：
conversation_agent: 对话智能体对象
conversation_config: 对话智能体的配置字典
"""
sessions_context_register = {}


# 总结智能体的系统提示词和PromptTemplate
summarize_system_prompt = """你是一个强大且专业的总结助手，能够将冗长的文本内容提炼为简洁明了的摘要。
注意要使用尽可能少的文字，同时又要尽可能保持原文的主旨和关键信息。
"""
summarize_prompt = """请将对话内容总结为简洁明了的摘要（注意保留原文主旨和关键信息）。"""

# 总结智能体，用于将过长的上下文进行总结压缩
summarize_agent = create_agent(
    model=conversation_llm,
    tools=[],
    system_prompt=summarize_system_prompt,
)


async def compress_context(context: List[BaseMessage]) -> str:
    """
    如果上下文过长，则使用总结智能体进行压缩。
    :param context: 原始上下文字符串
    :return: 压缩后的上下文字符串
    """
    # 构造新的消息列表用于调用总结智能体，避免修改原始 context 列表
    invoke_messages = context + [HumanMessage(content=summarize_prompt)]
    logging.info("总结智能体压缩上下文中...")
    response = await summarize_agent.ainvoke(
        input={ "messages": invoke_messages }
    )

    # 分析 response 的类型，尽量稳健地提取内容
    if isinstance(response, AIMessage):
        compressed_context = response.content
    elif isinstance(response, str):
        compressed_context = response
    elif isinstance(response, tuple):
        msg, meta = response[0], response[1]
        compressed_context = msg.content
    else:
        compressed_context = str(response)

    return compressed_context


async def manage_context(state: ConversationState, config: RunnableConfig):
    """
    管理对话上下文。如果上下文过长，则进行总结压缩。
    :param state: 当前对话状态
    :param config: 当前对话配置
    """
    logging.info("已进入上下文管理结点...")
    # 计算当前上下文的长度
    messages = state.get("messages", [])
    if len(messages) > 1 and isinstance(messages[-1], HumanMessage):
        messages_to_compress = messages[:-1]  # 不包括最后一条用户消息
    elif len(messages) > 2 and isinstance(messages[-1], AIMessage):
        messages_to_compress = messages[:-2]  # 不包括最后一条AI消息和最后一条用户消息
    else:
        messages_to_compress = messages

    if not messages_to_compress:
        logging.info("当前所需压缩的上下文为空，无需管理。")
        return {}

    need_compress = False   # 是否需要压缩的标志
    try:
        # 计算当前上下文的Token数量
        context_token_count = conversation_llm.get_num_tokens_from_messages(messages_to_compress)
        # 获取设定的Token阈值
        max_tokens = state.get("max_tokens", CONVERSATION_MAX_TOKENS)
        logging.info(f"当前上下文的Token数量为 {context_token_count}，设定阈值为 {max_tokens}。")
        if context_token_count >= max_tokens:
            need_compress = True
    except Exception as e:
        logging.error(f"计算上下文Token数量时出现异常: {e}")
        logging.info(f"将尝试使用对话轮数限制上下文长度。")
        # 获取设定的对话轮数阈值
        max_dialogues = state.get("max_dialogues", CONVERSATION_MAX_DIALOGUES)
        # 如果计算Token数量失败，则使用对话轮数进行限制
        if len(messages_to_compress) >= 2 * max_dialogues:   # 可压缩的对话轮数超过指定轮数则压缩
            need_compress = True
    # 如果上下文过长，超过了设定的token阈值，则进行总结压缩
    if need_compress:
        # 上下文过长，进行总结压缩
        logging.info("上下文过长，开始进行总结压缩...")
        compressed_context = await compress_context(messages_to_compress)
        logging.info("上下文总结压缩完成。")

        # 使用RemoveMessage清空原有消息，只保留压缩后的摘要作为新的上下文
        # 注意：RemoveMessage 只会删除指定ID的消息在当前Graph的state中的数据，而不会修改数据库中的记录
        # 但是这不会导致重启会话加载原本删除的上下文，因为checkpointer加载最后一次保存的状态（checkpoint）时，已经不包含这些消息了
        remove_messages = [RemoveMessage(id=msg.id) for msg in messages_to_compress]
        new_messages = remove_messages + [AIMessage(content=compressed_context)]

        return {
            "summary": compressed_context,
            "messages": new_messages
        }
    else:
        logging.info("当前上下文长度未超出阈值，无需压缩。")
    # 上下文未超出阈值，无需压缩，state不需要更新
    return {}


async def call_agent(state: ConversationState, config: RunnableConfig):
    """
    调用对话智能体，处理用户输入并生成响应。
    :param state: 当前对话状态
    :param config: 当前对话配置
    :return: 更新后的对话状态
    """
    logging.info("已进入调用对话智能体结点...")
    # 获取agent
    agent = config.get("configurable", {}).get("chat_agent", None)
    # 获取消息输出队列
    queue = config.get("configurable", {}).get("queue", None)
    if agent is None:
        raise RuntimeError("对话智能体尚未初始化，请先调用 init_conversation_agent 函数。")
    if queue is None:
        raise RuntimeError("消息输出队列尚未初始化，请先确保在 config['configurable'] 中传入了 queue 对象。")

    logging.info("开始调用对话智能体处理用户输入...")
    # 流式调用agent，将输出的chunk放入队列
    try:
        # 将state中的上下文和用户新的输入拼接成一个列表
        history_messages = state.get("messages", "")
        user_input = state.get("input", "")
        input_messages = history_messages + [HumanMessage(content=user_input)]
        final_answer = ""
        # 使用拼接而成的消息列表调用agent
        # 这里调用没有传入 config，不需要agent内部记忆上下文，上下文由外部的Graph管理，通过state传入
        async for chunk in agent.astream(
            input={
                "messages": input_messages
            },
            stream_mode="messages"
        ):
            await queue.put(chunk)
            # 逐步构建最终答案
            if isinstance(chunk, (list, tuple)):
                msg, meta = chunk[0], chunk[1]
                if (not isinstance(meta, dict)) or (not isinstance(msg, AIMessage)):
                    continue
                final_answer += msg.content

        # 返回最终答案
        return {
            "messages": [AIMessage(content=final_answer)],
            "final_answer": final_answer
        }

    except Exception as e:
        logging.error(f"call_agent结点出现异常: {e}")
        raise e


"""
定义对话Graph，实现可持久化且上下文长度可控的对话工作流。
结点manage_context用于管理上下文长度，结点call_agent用于调用对话智能体。
"""
conversation_graph = StateGraph(state_schema=ConversationState)

# 结点定义
conversation_graph.add_node("manage_context", manage_context)
conversation_graph.add_node("call_agent", call_agent)

# 边定义
# 这里START结点同时连接到manage_context和call_agent这两个异步方法，可以做到两个结点并发执行。
# 这样的好处是manage_context结点如果要总结上下文，该操作不会阻塞call_agent结点的执行，从而提升响应速度和用户体验。
conversation_graph.add_edge(START, "manage_context")
conversation_graph.add_edge(START, "call_agent")
conversation_graph.add_edge("manage_context", END)
conversation_graph.add_edge("call_agent", END)

# 全局的对话Graph执行器实例，采用懒加载的方式初始化
conversation_graph_executor: CompiledStateGraph[StateT, ContextT, InputT, OutputT] = None
conversation_graph_executor_with_checkpointer: CompiledStateGraph[StateT, ContextT, InputT, OutputT] = None


async def init_graph_executor():
    """
    获取对话Graph的执行器实例，采用懒加载的方式。
    :return: Conversation Graph的执行器实例
    """
    global conversation_graph_executor, conversation_graph_executor_with_checkpointer
    # 获取初始化锁，确保多协程并发安全
    async with init_lock:
        # 双重检查，确保在获取锁期间没有其他线程已经初始化了executor
        if conversation_graph_executor_with_checkpointer is None:
            # 使用定义好的 conversation_graph 编译执行器，传入 checkpointer 以实现对话状态持久化
            conversation_graph_executor_with_checkpointer = conversation_graph.compile(
                checkpointer=await utils.get_pooled_checkpointer(),
            )
            logging.info("Conversation Graph Executor With Checkpointer 初始化完成。")
        
        if conversation_graph_executor is None:
            # 不使用checkpointer的executor，适用于不需要持久化的临时会话
            conversation_graph_executor = conversation_graph.compile()
            logging.info("Conversation Graph Executor Without Checkpointer 初始化完成。")


async def init_conversation_agent(thread_id: str,
                                  resume_summary_text: str,
                                  jd_summary_text: str,
                                  match_score: int,
                                  differences: str,
                                  improvement_suggestions: str,
                                  job_hunting_advice: str):
    """
    初始化对话智能体，并创建一个临时会话的config
    :param thread_id: 会话ID。用于保存和加载与agent会话的上下文。
    :param resume_summary_text: 简历摘要文本
    :param jd_summary_text: 职位描述摘要文本
    :param differences: 简历与职位描述的差异点
    :param match_score: 匹配度分数
    :param improvement_suggestions: 简历改进建议
    :param job_hunting_advice: 求职建议
    :return: 包含会话配置的字典

    Args:
        thread_id:
        thread_id:
    """
    global global_mcp_tools
    global get_tools_task
    # 如果全局MCP工具列表还没被初始化，并且也没有其他线程开启获取MCP工具的异步任务，就开启一个异步获取MCP工具列表的任务
    if global_mcp_tools is None and get_tools_task is None:
        # 获取初始化锁，确保多协程并发安全
        async with init_lock:
            # 双重检查，确保在获取锁期间没有其他线程已经创建了任务
            if global_mcp_tools is None and get_tools_task is None:
                get_tools_tasks = []
                for mcp_client in mcp_clients:
                    # 注意要判断 get_tools_task 是否为 None，避免重复创建任务
                    task = asyncio.create_task(mcp_client.get_tools())
                    if task is not None:
                        get_tools_tasks.append(task)
                # 合并所有MCP工具获取任务为一个任务
                if get_tools_tasks:
                    get_tools_task = asyncio.gather(*get_tools_tasks, return_exceptions=True)
                else:
                    get_tools_task = None

    # 根据输入参数，利用system prompt生成对话智能体的系统提示词
    # 根据各种参数的情况，判断用户的身份
    if (improvement_suggestions.strip() != "") or (job_hunting_advice.strip() != ""):
        # 用户是求职者
        user_role = "求职者"
    elif differences.strip() != "":
        # 用户是招聘者
        user_role = "招聘者"
    else:
        # 用户身份未知
        user_role = "未知"
    conversation_system_prompt = conversation_system_prompt_template.format(
        user_role=user_role,
        resume_summary_text=resume_summary_text,
        jd_summary_text=jd_summary_text,
        match_score=match_score,
        differences=differences,
        resume_advice=improvement_suggestions,
        job_hunting_advice=job_hunting_advice
    )

    # 生成一个会话ID，用于临时会话
    conversation_config = {
        "configurable": {
            "thread_id": str(thread_id)
        }
    }

    # 从之前开启的异步任务中，获取MCP工具
    agent_tools = []
    if global_mcp_tools is None:
        # 尝试从异步任务中获取MCP工具列表
        # 如果获取失败，则记录错误日志，并继续初始化对话智能体（不使用MCP工具）
        # 但是不会将空列表记录到global_mcp_tools中，以便后续继续重试获取MCP工具
        try:
            # 如果 get_tools_task 仍然是 None (说明没有 client)，则跳过 await
            if get_tools_task:
                mcp_tool_futures = await get_tools_task
                mcp_tools = []
                for future in mcp_tool_futures:
                    if isinstance(future, Exception):
                        logging.error(f"获取MCP工具时出现异常: {future}\n将不使用该MCP工具继续初始化对话智能体。")
                        continue
                    else:
                        mcp_tools.extend(future)
                global_mcp_tools = mcp_tools  # 缓存结果
            else:
                mcp_tools = []
        except Exception as e:
            logging.error(f"获取MCP工具失败: {e}\n将不使用MCP工具继续初始化对话智能体。")
            mcp_tools = []
            # 显式重置任务句柄，确保下一次请求能正确触发新的 create_task
            get_tools_task = None
    else:
        mcp_tools = global_mcp_tools
    agent_tools.extend(mcp_tools)

    # 创建对话智能体
    # 该agent不传入记忆组件，是无状态的。所有上下文均由外部Graph通过state传入和统一管理
    conversation_agent = create_agent(
        model=conversation_llm,
        tools=agent_tools,
        system_prompt=conversation_system_prompt,
    )

    # 直接返回对象，不再设置 contextvars
    return conversation_agent, conversation_config


async def invoke_agent_in_background(queue: asyncio.Queue, message: str, conversation_agent, config):
    """
    当用户输入完毕，发起一次调用后，在后台运行agent，并将流式输出块放入队列。
    """
    try:
        if conversation_agent is None:
            raise RuntimeError("对话智能体尚未初始化，请先调用 init_conversation_agent 函数。")

        # 使用 stream_mode="messages" 以获得消息流块
        async for chunk in conversation_agent.astream(
            input={
                "messages": [HumanMessage(content=message)]
            },
            config=config,
            stream_mode="messages",
        ):
            await queue.put(chunk)

    except Exception as e:
        await queue.put({"error": str(e)})
    finally:
        # 结束信号
        await queue.put(None)


async def invoke_conversation_graph_in_background(
    queue: asyncio.Queue, 
    message: str, 
    conversation_agent: CompiledStateGraph[TypedDict, ContextT, _InputAgentState, TypedDict], 
    graph_executor: CompiledStateGraph[StateT, ContextT, InputT, OutputT], 
    config: dict
):
    """
    当用户输入完毕，发起一次调用后，在后台运行Conversation Graph，并将流式输出块放入队列。
    """
    # 确保初始化了 conversation_graph_executor_with_checkpointer
    if graph_executor is None:
        await init_graph_executor()

    # 构造初始状态
    initial_state = ConversationState(
        messages=[],
        max_tokens=20000,   # 设置上下文的最大Token数阈值
        max_dialogues=8,    # 设置上下文的最大对话轮数阈值
        summary="",
        input=message,
        final_answer="",
    )
    
    # 将不可序列化的对象放入 configurable 中
    run_config = config.copy()
    if "configurable" not in run_config:
        run_config["configurable"] = {}
    else:
        run_config["configurable"] = run_config["configurable"].copy()
    
    run_config["configurable"]["chat_agent"] = conversation_agent
    run_config["configurable"]["queue"] = queue

    # 使用指定的 config 调用 Conversation Graph
    try:
        await graph_executor.ainvoke(
            input=initial_state,
            config=run_config
        )
    except Exception as e:
        await queue.put({"error": str(e)})
    finally:
        # 结束信号
        await queue.put(None)


def _message_to_text(msg) -> str:
    """
    尽量稳健地提取 BaseMessage 的文本内容。
    注意：不要对 content 做 strip 操作！否则会导致空格、换行符、制表符等字符丢失，从而影响输出内容的可读性。
    :param msg: BaseMessage 对象
    :return: 提取的文本内容，str类型
    """
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # 兼容多 part 的消息内容
        parts = []
        for p in content:
            if isinstance(p, dict):
                # 常见格式：{"type": "text", "text": "..."}
                txt = p.get("text")
                if isinstance(txt, str):
                    parts.append(txt)
                else:
                    parts.append(str(p))
            else:
                parts.append(str(p))
        return "\n".join(parts)
    return str(content)


async def chat_with_agent(message: str, history: list, request: gradio.Request):
    """
    Gradio 回调：启动后台任务并消费队列，yield 给前端。
    :param message: 用户输入的消息
    :param history: 对话历史
    :param request: Gradio 请求对象，可以从中获取session_hash等请求信息
    :return: 异步生成器，yield 流式输出块
    """
    
    task = None
    try:
        
        # 确保初始化了 conversation_graph_executor_with_checkpointer
        if conversation_graph_executor_with_checkpointer is None:
            await init_graph_executor()
        
        # 获取当前用户的唯一会话 ID (对应浏览器的一个 Tab)
        session_id = request.session_hash

        # 2. 获取 URL 中的参数 (用于定位预先生成的数据)
        # 假设 URL 是 http://localhost:7860/?analysis_id=1
        params = request.query_params
        analysis_id = params.get("analysis_id", "")  # 获取 analysis_id 参数（如果不存在则用空字符串代替）

        logging.info(f"收到来自 session_id: {session_id} 的请求, analysis_id: {analysis_id}")
        
        graph_need_memory = True  # Graph默认需要记忆功能
        if analysis_id == "":
            logging.info(f"Session {session_id} 未提供 analysis_id 参数，进入无预生成数据的临时会话模式。")
            graph_need_memory = False  # 没有 analysis_id，说明没有预生成数据，进入临时会话模式，不需要记忆功能

        # 判断对话智能体是否已经被初始化。如果没有就调用init_conversation_agent
        # 需要注意init_conversation_agent方法所需的参数从thread_local中获取
        if analysis_id not in sessions_context_register:
            logging.info("对话智能体尚未初始化! 尝试初始化对话智能体中...")

            # --- 数据获取逻辑 ---
            # 首先查询 Redis 中的 Cuckoo Filter，如果过滤器中不存在该 analysis_id，则说明没有对应的预生成数据
            hasFilter = True if redis_client.exists(RESUME_ANALYSIS_CUCKOO_FILTER_REDIS_KEY) == 1 else False
            if hasFilter and (not redis_client.cf().exists(RESUME_ANALYSIS_CUCKOO_FILTER_REDIS_KEY, str(analysis_id))):
                logging.info(f"Redis Cuckoo Filter中不存在 analysis_id: {analysis_id}，将不使用预生成数据初始化智能体。")
                resume_summary_text = ""
                jd_summary_text = ""
                differences = ""
                match_score = -1
                improvement_suggestions = ""
                job_hunting_advice = ""
            else:
                if not hasFilter:
                    logging.error(f"Redis中不存在 Cuckoo Filter，Key: {RESUME_ANALYSIS_CUCKOO_FILTER_REDIS_KEY}。"
                                  f"跳过过滤器检查，开始尝试从Redis中获取预生成数据初始化智能体。")
                else:
                    logging.info(f"Redis Cuckoo Filter中存在 analysis_id: {analysis_id}，尝试使用预生成数据初始化智能体。")

                # 从 Redis 中获取预生成的数据
                redis_key = get_resume_analysis_redis_key(analysis_id)
                logging.info(f"尝试从Redis中获取预生成数据，以初始化智能体。Redis Key: {redis_key}")
                init_data = redis_client.hgetall(redis_key)

                if init_data and init_data != {}:
                    logging.info(f"在Redis中发现预生成数据，Redis Key: {redis_key}")

                    resume_summary_text = init_data.get("resume_summary_text", "")
                    jd_summary_text = init_data.get("jd_summary_text", "")
                    differences = init_data.get("differences", "")
                    match_score = init_data.get("match_score", -1)
                    improvement_suggestions = init_data.get("improvement_suggestions", "")
                    job_hunting_advice = init_data.get("job_hunting_advice", "")
                    # 刷新过期时间
                    redis_client.expire(redis_key, RESUME_ANALYSIS_REDIS_TTL)

                else:
                    # Redis中没能找到预生成数据，尝试从MySQL中获取
                    is_exist = True
                    with mysql_engine.connect() as connection:
                        logging.info(f"Redis中未找到预生成数据，尝试从MySQL中获取。分析记录ID: {analysis_id}")
                        logging.info(f"正在查询表 tb_resume_analysis 中的预生成数据，分析记录ID: {analysis_id}")
                        result = connection.execute(
                            text("""SELECT analysis_result 
                                    FROM tb_resume_analysis 
                                    WHERE id = :id"""),
                            {"id": analysis_id}
                        )
                        row = result.fetchone()
                        if row:
                            # 从Row对象中获取analysis_result字段的值，并解析为JSON
                            analysis_result_str = row.analysis_result
                            analysis_result_json: dict = json.loads(analysis_result_str)
                            logging.info(f"tb_resume_analysis表中发现预生成数据，分析记录ID: {analysis_id}")
                            match_score = analysis_result_json.get("match_score", -1)
                            differences = analysis_result_json.get("differences", "")
                            improvement_suggestions = analysis_result_json.get("improvement_suggestions", "")
                            job_hunting_advice = analysis_result_json.get("job_hunting_tips", "")
                        else:
                            logging.info(f"tb_resume_analysis表中未找到预生成数据，分析记录ID: {analysis_id}")
                            match_score = -1  # 使用 -1 表示无效分数
                            differences = ""
                            improvement_suggestions = ""
                            job_hunting_advice = ""
                            is_exist = False

                        logging.info(f"正在查询表 tb_analysis_summary 中的预生成数据，分析记录ID: {analysis_id}")
                        result = connection.execute(
                            text("""SELECT resume_summary_text, jd_summary_text 
                                    FROM tb_analysis_summary 
                                    WHERE analysis_id = :id"""),
                            {"id": analysis_id}
                        )
                        row = result.fetchone()
                        if row:
                            logging.info(f"tb_analysis_summary中发现预生成数据，分析记录ID: {analysis_id}")
                            resume_summary_text = row.resume_summary_text or ""
                            jd_summary_text = row.jd_summary_text or ""
                        else:
                            logging.info(f"tb_analysis_summary中未找到预生成数据，记录分析ID: {analysis_id}")
                            resume_summary_text = ""
                            jd_summary_text = ""
                            is_exist = False
                        # 如果从MySQL中成功获取到了预生成数据，则将其存入Redis，便于下次快速获取
                        if is_exist:
                            logging.info(f"从MySQL中成功获取到预生成数据，正在缓存到Redis中。Redis Key: {redis_key}")
                            # 将查询结果存入Redis，便于下次快速获取
                            redis_client.hset(redis_key, mapping={
                                "resume_summary_text": resume_summary_text,
                                "jd_summary_text": jd_summary_text,
                                "differences": differences,
                                "match_score": match_score,
                                "improvement_suggestions": improvement_suggestions,
                                "job_hunting_advice": job_hunting_advice,
                            })
                            redis_client.expire(redis_key, RESUME_ANALYSIS_REDIS_TTL)  # 设置过期时间
                            logging.info(f"预生成数据已成功缓存到Redis。Redis Key: {redis_key}")
                        else:
                            # 如果MySQL中没能够获取到预生成数据，则在Redis中插入一个空记录，避免缓存穿透
                            logging.info(f"未能从MySQL中获取到预生成数据。分析记录ID: {analysis_id}")
                            logging.info(f"将不使用预生成数据初始化智能体...")
                            redis_client.hset(redis_key, mapping={})
                            redis_client.expire(redis_key, NULL_REDIS_TTL)  # 设置过期时间

            logging.info("对话智能体正在初始化...")

            agent, config = await init_conversation_agent(
                analysis_id,
                resume_summary_text=resume_summary_text,
                jd_summary_text=jd_summary_text,
                match_score=match_score,
                differences=differences,
                improvement_suggestions=improvement_suggestions,
                job_hunting_advice=job_hunting_advice,
            )

            # 将 Agent 和 Config 存入全局字典，实现持久化。
            # 使用analysis_id作为键，确保每个分析记录的会话是独立的。
            sessions_context_register[analysis_id] = {
                "conversation_agent": agent,
                "conversation_config": config
            }
            logging.info("对话智能体初始化完成。")

        # 从全局字典中获取当前用户的 Agent 和 Config
        user_context = sessions_context_register[analysis_id]
        conversation_agent = user_context["conversation_agent"]
        config = user_context["conversation_config"]

        queue = asyncio.Queue()
        
        if graph_need_memory:
            logging.info(f"会话 {session_id} 需要记忆功能，将使用持久化的 Conversation Graph Executor With Checkpointer。")
            graph_executor = conversation_graph_executor_with_checkpointer
        else:
            logging.info(f"会话 {session_id} 不需要记忆功能，将使用不带持久化的 Conversation Graph Executor。")
            graph_executor = conversation_graph_executor

        # 启动后台任务，让模型根据用户的输入生成回复（不要await，应该用asyncio在事件循环中添加一个新的任务，且当前协程不等待它）
        task = asyncio.create_task(invoke_conversation_graph_in_background(queue, message, conversation_agent, graph_executor, config))

        full_response = ""

        # 如果你不想占位文本，可以移除下面两行，但务必在结束前确保至少 yield 一次。
        # placeholder = "正在处理，请稍候..."
        # yield placeholder
        output_once = False

        while True:
            chunk = await queue.get()

            # 结束信号
            if chunk is None:
                if not output_once:
                    # 若没有任何产出，最后至少返回一句，避免 StopAsyncIteration
                    yield "抱歉，没有产生可显示的输出。"
                break

            # 错误通道
            if isinstance(chunk, dict) and "error" in chunk:
                while True:
                    yield f"抱歉，处理时出现错误: {chunk['error']}"
                    chunk = await queue.get()
                    if chunk is None:
                        break
                break

            # 仅处理形如 (BaseMessage, metadata) 的AIMessage流块
            if isinstance(chunk, (list, tuple)):
                msg, meta = chunk[0], chunk[1]
                if (not isinstance(meta, dict)) or (not isinstance(msg, AIMessage)):
                    continue

                final_text = _message_to_text(msg)
                if final_text:
                    full_response += final_text
                    yield full_response
                    output_once = True

    except Exception as e:
        logging.error(f"chat_with_agent 回调出现异常: {e}")
        yield f"抱歉，处理时出现错误: {e}"

    finally:
        # 确保后台任务结束（若仍在运行则取消）
        if task and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def cleanup_session_context(request: gradio.Request):
    """
    Gradio 回调：清理会话上下文。
    :param request: Gradio 请求对象，可以从中获取session_hash等请求信息
    """
    if not request:
        return      # 无请求对象，无法获取请求参数

    session_id = request.session_hash
    params = request.query_params
    analysis_id = params.get("analysis_id", "")  # 获取 analysis_id 参数
    if analysis_id in sessions_context_register:
        try:
            # 删除当前会话对应的 agent 和 config
            del sessions_context_register[analysis_id]
            logging.info(f"用户断开连接，已清理 session_id: {session_id} ，analysis_id: {analysis_id} 的会话资源。")
            logging.info(f"当前剩余活跃会话数: {len(sessions_context_register)}")
        except Exception as e:
            logging.error(f"清理 session_id: {session_id} 的会话资源时出错，analysis_id: {analysis_id}: {e}")


def mock_data():
    # 如需使用mock数据测试，可以在gradio启动后访问 http://localhost:7860/?analysis_id=16
    thread_resume_summary_text.set(f"""姓名: 项炎
    年龄: 37
    教育背景: 学校: 北京科技经营管理学院; 学位: 学士学位; 毕业年份: 2010.06
    工作经验: 2007.03-2010.07：广州云蝶科技有限公司，产品开发，负责Unity场景搭建、灯光渲染、性能优化等工作; 2005.04-2018.04：前程无忧（长沙），试剂生产员（生物），负责行政支持、物资管理、档案整理等工作; 1990.06-2016.12：T3出行，诉讼部诉讼秘书，负责运营文件起草、制度监控、销售报表分析等工作; 2007.06-2017.02：嘉展国际，财务业务员，负责医药产品招商推广、市场规划、代理商管理等工作
    项目经历: 2000.04-2011.04：信息化条件下宣传思想工作研究，负责多媒体运营渠道拓展、广告资源整合等工作; 2006.05-2013.12：自媒体时代主流意识形态话语面临的挑战及对策研究，协调拍摄资源、解决拍摄问题等工作; 2006.01-2010.10：岭南文化融入大学生思想政治教育研究，负责台账管理、客户资料归档、人事工作等
    专业技能: Unity场景搭建与渲染; 游戏性能优化; 行政管理与协调; 市场推广与销售; 多媒体运营与广告投放; 项目协调与资源管理
    求职目标: 前端开发
    相关证书: 未提供
    综合素质总结: 项炎拥有3年工作经验，学士学位，擅长Unity开发、行政管理、市场推广等多领域工作。在前端开发领域有明确的职业目标，具备较强的项目协调和资源管理能力。
    """)
    thread_jd_summary_text.set(f"""职位名称: "前端开发工程师"
    公司名称: "Tech Innovators Ltd."
    工作地点: "北京"
    职位职责: 负责公司网站和应用的前端开发与维护; 与设计团队合作，实现高质量的用户界面; 优化网站性能，提升用户体验; 参与需求分析和技术方案制定
    职位要求: 熟悉JavaScript、HTML、CSS等前端技术; 有React或Vue.js等主流框架的开发经验; 具备良好的代码编写习惯和团队合作精神; 有相关项目经验者优先考虑
    职位福利: 具有竞争力的薪资待遇; 弹性工作时间和远程办公选项; 完善的培训和职业发展机会; 丰富的员工活动和团队建设活动
    职位描述总结: Tech Innovators Ltd.正在北京招聘一位经验丰富的前端开发工程师，负责网站和应用的前端开发与维护，
    要求熟悉JavaScript、HTML、CSS等前端技术，并有React或Vue.js等框架的开发经验。
    公司提供具有竞争力的薪资待遇、弹性工作时间、远程办公选项以及完善的培训和职业发展机会。
    """)
    thread_match_score.set(20)
    thread_resume_advice.set("""您的简历显示出丰富的跨领域经验，但需更加突出与前端开发相关的技能和经历。
        建议将前端技能（如 JavaScript、HTML、CSS）放在显眼位置，若有前端项目经验可加以展示，或提到您自学的相关内容。
        Unity开发的背景可以保留，但不必过多占据篇幅。强化您在项目协调和团队合作方面的能力，这对前端开发工作有帮助。
        最后，优化求职目标，明确表明您希望转向前端开发。
        """)
    thread_job_hunting_advice.set("""建议加快提升前端核心技能，特别是 JavaScript、React 或 Vue.js 等框架，通过开源项目或自学积累实战经验。
        同时，发挥您在项目管理和团队合作上的优势，突出跨团队沟通能力。
        获取相关证书或参加前端培训，将增加您的竞争力。
        """)


def start_bot_interface():
    # 自定义CSS样式
    # 使用多行字符串可以方便地编写CSS
    custom_css = """
    /* 将整个页面的背景设置为深灰色 */
    body {
        background-color: #2b2b2b !important;
    }

    /* 强制将标题文字颜色设置为白色 */
    .gradio-container h1.gr-title {
        color: white !important;
    }

    /* (可选) 将描述文字颜色也设置为浅灰色，且位置居中，以提高可读性 */
    .gradio-container .gr-description p {
        color: #f0f0f0 !important;
        text-align: center !important;
    }
    """
    # 自定义给 Chatbot 组件
    chatbot = gradio.Chatbot(
        type="messages",
        render_markdown=True,  # 启用 Markdown 渲染
        height=600,  # 聊天区域高度设置为600像素
        show_copy_button=True,  # 显示复制按钮
    )
    # 自定义 Textbox 组件
    textbox = gradio.Textbox(
        placeholder="请输入你的问题...",  # 占位符文本
        lines=1,  # 初始行数为1行
        max_lines=9,  # 最大行数为9行
        container=False,  # 不使用额外的容器
        submit_btn=True,    # 提交按钮
        stop_btn=True,   # 停止按钮
    )
    # --- Gradio 界面 ---
    bot_interface = gradio.ChatInterface(
        fn=chat_with_agent,
        chatbot=chatbot,
        fill_height=True,  # 让聊天区域填满可用高度
        textbox=textbox,
        type="messages",
        title="🤖 简历-职位 分析助理",
        description="一个基于智能体的简历-职位分析助手，能够帮助你详细分析简历和职位描述的匹配度，并提供给你有价值的建议和指导。",
        examples=[
            ["我的简历与目标岗位匹配度较低，是否应该调整目标？"],
            ["根据我的简历，推荐一下适合我投递的公司"],
            ["根据我的简历和目标职位描述，你觉得我在面试中需要注意哪些方面？"],
        ],
        theme="soft",  # 1. 先设置一个好的暗色主题作为基础
        css=custom_css,  # 2. 再用自定义CSS进行自定义
    )
    # 注册 unload 事件，该事件在用户关闭标签页时触发，会自动调用传入的回调方法
    bot_interface.unload(cleanup_session_context)
    try:
        # 尝试使用端口 7860 启动 Gradio 应用
        bot_interface.launch(server_name="0.0.0.0", server_port=7860)
    except RuntimeError as e:
        logging.error(f"简历分析助手出现运行异常: {e}\n")
        raise e
    finally:
        # 无论如何都确保执行完毕或异常后关闭服务连接
        bot_interface.close()


if __name__ == "__main__":
    start_bot_interface()
