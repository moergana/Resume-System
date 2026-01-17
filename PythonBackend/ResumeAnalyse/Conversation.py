import asyncio
import contextlib
import logging
import uuid
from typing import TypedDict

import gradio
from langchain.agents import create_agent
from langchain.agents.middleware.types import _InputAgentState
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph.state import CompiledStateGraph
from langgraph.typing import ContextT

from ResumeAnalyse import utils
from ResumeAnalyse.constants import get_resume_analysis_redis_key
from ResumeAnalyse.entity.thread_local import thread_resume_summary_text, thread_job_hunting_advice, \
    thread_jd_summary_text, thread_match_score, \
    thread_resume_advice
from ResumeAnalyse.utils import redis_client

Model_Name = "mistralai/devstral-2512:free"
Base_URL = "https://openrouter.ai/api/v1"
conversation_llm = init_chat_model(
    model=Model_Name,
    base_url=Base_URL,
    model_provider="openai",
    api_key=utils.openrouter_api_key,
)

# 对话智能体的系统提示词
conversation_system_prompt_template = PromptTemplate.from_template(template=
"""你是一个专业的求职助手，能够帮助用户分析简历和职位描述，提供有价值的建议和指导。请根据用户提供的信息，回答相关问题并提供实用的建议。

请注意你拥有以下工具：
1. 网络搜索工具：可以帮助你获取最新的新闻、信息和数据，特别是在你遇到不熟悉的领域或者不确定的问题时，可以通过调用网络搜索工具来获取最新的信息，并以此辅助你更好地回答用户的问题。
2. 地图工具：可以帮助你查询地理位置、路径规划、天气查询等信息。
3. 网页解析工具：可以帮助你从网页中提取有用的信息。
你需要根据用户的请求，智能地判断是否需要调用工具，应该调用哪个或哪些工具。
例如：
用户的请求为“请帮我搜索一下最近的科技新闻”，你应该调用网络搜索工具来完成任务。
用户的请求为“请帮我查看https://www.google.com/这个网页，并告诉我这个网页的内容”，你应该调用网页解析工具来完成任务。
...
记住：如果调用了工具，将工具返回的信息加以思考和整理之后再反馈给用户。

用户的背景信息：
1. 用户的简历内容概述如下：
{resume_summary_text}

2. 用户的目标职位描述内容概述如下：
{jd_summary_text}

3. 用户经过智能简历分析系统，目前得到的分析结果如下：
简历与职位描述的匹配度分数（百分制。如果是负数则表示分数无效，请忽略它）：{match_score}
简历与职位描述的差异点（如果为空，请忽略该字段）：{differences}
简历改进建议（如果为空，请忽略该字段）：{resume_advice}
求职建议（如果为空，请忽略该字段）：{job_hunting_advice}

接下来的对话过程中，你需要根据以上信息，回答用户提出的问题，并提供有价值的建议和指导。
"""
)

# MCP服务配置类，可以选择接入多个MCP工具
mcp_client = MultiServerMCPClient(
    {
        # "TongyiWebSearch": tongyi_web_search_mcp_config,
        # "AmapMaps": amap_maps_mcp_config,
        # "TongyiWebParser": tongyi_web_parser
    }
)

# 对话智能体对象（全局变量）
# conversation_agent: CompiledStateGraph[TypedDict, ContextT, _InputAgentState, TypedDict] = None


class SessionContext(TypedDict):
    conversation_agent: CompiledStateGraph[TypedDict, ContextT, _InputAgentState, TypedDict]
    conversation_config: dict


"""
登记当前会话的上下文信息。目前每个会话需要记录的信息如下：
conversation_agent: 对话智能体对象
conversation_config: 对话智能体的配置字典
"""
sessions_context_register = {}


async def init_conversation_agent(resume_summary_text: str,
                                  jd_summary_text: str,
                                  match_score: int,
                                  differences: str,
                                  improvement_suggestions: str,
                                  job_hunting_advice: str):
    """
    初始化对话智能体，并创建一个临时会话的config
    :param resume_summary_text: 简历摘要文本
    :param jd_summary_text: 职位描述摘要文本
    :param match_score: 匹配度分数
    :param improvement_suggestions: 简历改进建议
    :param job_hunting_advice: 求职建议
    :return: 包含会话配置的字典
    """

    conversation_system_prompt = conversation_system_prompt_template.format(
        resume_summary_text=resume_summary_text,
        jd_summary_text=jd_summary_text,
        match_score=match_score,
        differences=differences,
        resume_advice=improvement_suggestions,
        job_hunting_advice=job_hunting_advice
    )

    agent_tools = []
    mcp_tools = await mcp_client.get_tools()
    agent_tools.extend(mcp_tools)

    conversation_agent = create_agent(
        model=conversation_llm,
        tools=agent_tools,
        system_prompt=conversation_system_prompt,
        # checkpointer=await utils.get_checkpointer(),
        # store=await utils.get_store()
    )

    # 生成一个会话ID，用于临时会话
    thread_id = str(uuid.uuid4())
    conversation_config = {
        "configuration": {
            "thread_id": thread_id
        }
    }

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


def _message_to_text(msg) -> str:
    """
    尽量稳健地提取 BaseMessage 的文本内容。
    """
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content.strip()
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
        return "\n".join(parts).strip()
    return str(content).strip()


async def chat_with_agent(message: str, history: list, request: gradio.Request):
    """
    Gradio 回调：启动后台任务并消费队列，yield 给前端。
    :param message: 用户输入的消息
    :param history: 对话历史
    :param request: Gradio 请求对象，可以从中获取session_hash等请求信息
    :return: 异步生成器，yield 流式输出块
    """
    # 获取当前用户的唯一会话 ID (对应浏览器的一个 Tab)
    session_id = request.session_hash

    # 2. 获取 URL 中的参数 (用于定位预先生成的数据)
    # 假设 URL 是 http://localhost:7860/?user_id=123&resume_id=456&jd_id=789
    # 如需使用mock数据测试，可以在gradio启动后访问 http://localhost:7860/?user_id=mock_user&resume_id=mock_resume&jd_id=mock_jd
    params = request.query_params
    analysis_id = params.get("analysis_id", "")  # 获取 analysis_id 参数（如果不存在则用空字符串代替）

    logging.info(f"收到来自 session_id: {session_id} 的请求, analysis_id: {analysis_id}")

    # 判断对话智能体是否已经被初始化。如果没有就调用init_conversation_agent
    # 需要注意init_conversation_agent方法所需的参数从thread_local中获取
    if session_id not in sessions_context_register:
        logging.error("对话智能体尚未初始化!")

        # --- 数据获取逻辑 ---
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
            # ... 获取其他字段
        else:
            logging.warning("未找到预生成数据或未提供 Key\n将不附带简历分析数据启动对话智能体。")
            # 如果没有找到预生成数据，就使用空字符串或默认值
            resume_summary_text = ""
            jd_summary_text = ""
            match_score = -1  # 使用 -1 表示无效分数
            differences = ""
            improvement_suggestions = ""
            job_hunting_advice = ""

        logging.info("对话智能体正在初始化...")

        agent, config = await init_conversation_agent(
            resume_summary_text=resume_summary_text,
            jd_summary_text=jd_summary_text,
            match_score=match_score,
            differences=differences,
            improvement_suggestions=improvement_suggestions,
            job_hunting_advice=job_hunting_advice,
        )

        # 将 Agent 和 Config 存入全局字典，实现持久化
        sessions_context_register[session_id] = {
            "conversation_agent": agent,
            "conversation_config": config
        }
        logging.info("对话智能体初始化完成。")

    # 从全局字典中获取当前用户的 Agent 和 Config
    user_context = sessions_context_register[session_id]
    conversation_agent = user_context["conversation_agent"]
    config = user_context["conversation_config"]

    queue = asyncio.Queue()

    # 启动后台任务（不要await，应该用asyncio开启一个新的后台任务）
    task = asyncio.create_task(invoke_agent_in_background(queue, message, conversation_agent, config))

    full_response = ""

    # 如果你不想占位文本，可以移除下面两行，但务必在结束前确保至少 yield 一次。
    placeholder = "正在处理，请稍候..."
    yield placeholder
    output_once = False

    try:
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
                yield f"抱歉，处理时出现错误: {chunk['error']}"
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

    finally:
        # 确保后台任务结束（若仍在运行则取消）
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def cleanup_session_context(request: gradio.Request):
    """
    Gradio 回调：清理会话上下文。
    :param request: Gradio 请求对象，可以从中获取session_hash等请求信息
    """
    if not request:
        return # 无请求对象，无法获取 session_id

    session_id = request.session_hash
    if session_id in sessions_context_register:
        try:
            # 删除当前会话对应的 agent 和 config
            del sessions_context_register[session_id]
            logging.info(f"用户断开连接，已清理 session_id: {session_id} 的会话资源。")
            logging.info(f"当前剩余活跃会话数: {len(sessions_context_register)}")
        except Exception as e:
            logging.error(f"清理 session_id: {session_id} 的会话资源时出错: {e}")


def mock_data():
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
    )
    # --- Gradio 界面 ---
    bot_interface = gradio.ChatInterface(
        fn=chat_with_agent,
        chatbot=chatbot,
        fill_height=True,  # 让聊天区域填满可用高度
        textbox=textbox,
        title="🤖 简历-职位 分析助理",
        description="一个基于智能体的简历-职位分析助手，能够帮助你详细分析简历和职位描述的匹配度，并提供给你有价值的建议和指导。",
        examples=[
            ["我的简历与目标岗位匹配度较低，是否应该调整目标？"],
            ["根据我的简历，推荐一下适合我投递的公司"],
            ["根据我的简历和目标职位描述，你觉得我在面试中需要注意哪些方面？"],
        ],
        theme="gradio/dark",  # 1. 先设置一个好的暗色主题作为基础
        css=custom_css,  # 2. 再用自定义CSS进行自定义
    )
    # 注册 unload 事件，该事件在用户关闭标签页时触发，会自动调用传入的回调方法
    bot_interface.unload(cleanup_session_context)
    # 启动 Gradio 应用，监听所有网络接口
    bot_interface.launch(server_name="0.0.0.0")


if __name__ == "__main__":
    start_bot_interface()
