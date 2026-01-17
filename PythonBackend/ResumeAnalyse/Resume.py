import json
import logging
import os
from os.path import basename
from typing import List, Optional, Dict, Any

from chromadb import SparseVector
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredPDFLoader
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain_core.runnables import Runnable
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.constants import END
from langgraph.graph import StateGraph

from MultiAgentGraph import utils
from MultiAgentGraph.utils import OverallState, RESUME_AGENT_NAME

# OpenRouter 平台模型调用
Model_Name = "z-ai/glm-4.5-air:free"
Base_URL = "https://openrouter.ai/api/v1"


# 自定义嵌入模型类，用于将简历内容向量化
class ResumeEmbedding(Embeddings):
    """
    封装本地向量模型，默认使用 Qwen/Qwen3-Embedding-0.6B。
    """

    def __init__(self, model_name: str = "Qwen/Qwen3-Embedding-0.6B"):
        self.embeddings = SentenceTransformerEmbeddings(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)


# --- 全局组件初始化 ---

def initialize_resume_components(
        collection_name: str = "resume_collection",  # 向量数据库库的集合名称，不同的集合就像数据库中的不同表
        persist_dir: str = "/root/program_projects/LangGraph/MultiAgentGraph/documents",  # 集合数据的本地存储路径
        k: int = 5,  # Top-K 需要通过检索最终得到的最高相关性chunk的数量
) -> tuple[BaseChatModel, Embeddings, Chroma, Runnable]:
    """
    初始化简历分析所需的 LLM、历史感知 Retriever、结构化解析 prompt 等组件。
    """
    # 1. 初始化 LLM
    llm = init_chat_model(
        model=Model_Name,
        base_url=Base_URL,
        model_provider="openai",
        api_key=utils.openrouter_api_key,
    )

    # 2. 初始化 Embedding
    embeddings = ResumeEmbedding(model_name="Qwen/Qwen3-Embedding-0.6B")

    # 3. 初始化 Chroma 向量库（用于所有简历，按 metadata 区分）
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )

    # 4. 基础 Retriever（后面会用历史感知包装）
    base_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )

    # 5. 构建历史感知 Retriever 的 prompt
    query_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            content=(
                "你是一个专业的检索查询助手，负责根据当前对话历史与本轮问题，"
                "生成一个更适合在简历向量数据库中检索的查询。"
                "只输出新生成的检索查询本身，不要解释或添加无关的内容。"
            )
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template(
            "请基于以上对话历史与当前问题，生成一个优化后的检索查询。\n"
            "当前问题: {input}"
        ),
    ])

    history_aware_retriever = create_history_aware_retriever(
        llm=llm,
        retriever=base_retriever,
        prompt=query_prompt,
    )

    return llm, embeddings, vectorstore, history_aware_retriever


# 经过initialize_resume_components方法初始化得到的全局组件
# 包括 LLM、ResumeEmbedding、Chroma向量库、历史感知检索器
llm, resume_embeddings, resume_vectorstore, history_aware_retriever = initialize_resume_components()


def load_resume_documents(
        pdf_path: str,
        candidate_id: Optional[str] = None,
) -> List[Document]:
    """
    使用 UnstructuredPDFLoader 加载简历，并进行分块。
    可选：先用 PyMuPDFLoader 做预处理（例如获取页码、布局信息）。
    """
    assert os.path.exists(pdf_path), f"简历文件不存在: {pdf_path}"

    # 可选的布局分析（当前只演示如何获取 Document；如需进一步处理可在此扩展）
    try:
        layout_loader = PyMuPDFLoader(pdf_path)
        layout_docs = layout_loader.load()
        # 如果你要用布局信息，可以把 layout_docs 的元数据合并到下文 docs 中
        logging.info(f"PyMuPDFLoader 加载完成，共 {len(layout_docs)} 个文档片段。")
    except Exception as e:
        logging.warning(f"PyMuPDFLoader 加载失败，跳过布局分析: {e}")
        layout_docs = []

    # 使用 UnstructuredPDFLoader 提取简历PDF的内容
    # UnstructuredPDFLoader 自带OCR + 布局分析，对于简历这种结构化文档效果较好，表现也更加稳定
    # 这里使用 mode="elements" 以获得更细粒度的元素
    loader = UnstructuredPDFLoader(pdf_path, mode="elements")
    raw_docs = loader.load()
    logging.info(f"UnstructuredPDFLoader 加载完成，共 {len(raw_docs)} 个元素。")

    # 分块
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"],
    )
    split_docs = splitter.split_documents(raw_docs)

    # 增强 metadata
    # 这一步是为了支持多份简历存储在同一个向量库中，通过 metadata 来区分不同简历的来源
    base_name = os.path.basename(pdf_path)
    for d in split_docs:
        d.metadata.setdefault("source", base_name)
        if candidate_id:
            d.metadata.setdefault("candidate_id", candidate_id)

    logging.info(f"简历 {base_name} 分块完成，共 {len(split_docs)} 个 chunk。")
    return split_docs


def clean_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """
    将 UnstructuredPDFLoader 产生的复杂 metadata 里有用的信息手动展开为扁平字段。
    """
    # 这里设置的是清洗之后应该留下的类型列表，也是 Chroma中metadata 支持的类型
    target_types = (
        str,
        int,
        float,
        bool,
        SparseVector,
    )
    meta = dict(meta)  # 复制一份，避免原地修改带来副作用

    # 遍历所有的k-v对，将v类型不属于target_types内的字段全部转为str类型
    for k, v in meta.items():
        if not isinstance(v, target_types):
            meta[k] = str(v)

    return meta


def store_resume_to_vectorstore(
        pdf_path: str,
        candidate_id: Optional[str] = None,
):
    """
    将单份简历解析为分块后写入 Chroma 向量库存储。
    """
    docs = load_resume_documents(pdf_path, candidate_id=candidate_id)

    # 清洗直接通过UnstructuredPDFLoader得到的Documents
    # 由于其中包含复杂的metadata，而Chroma只支持一些简单的类型：str, int, float, bool, SparseVector, None
    # 因此需要过滤掉不支持的类型
    for d in docs:
        d.metadata = clean_metadata(d.metadata)

    # Chroma 0.4+自动持久化，无需手动 persist()
    resume_vectorstore.add_documents(docs)
    logging.info(f"简历 {pdf_path} 已写入向量库，candidate_id={candidate_id}")


def resume_embedding_node(state: OverallState) -> dict:
    """
    嵌入简历PDF结点：对指定 pdf_path 做嵌入并存储到向量库。
    该结点不是每次对话都必定执行，需要根据state中的状态量判断
    """
    need_embed = state.get("need_embed", {}).get(RESUME_AGENT_NAME, False)
    if not need_embed:
        return {}

    logging.info("--- 简历 RAG: 嵌入阶段 ---")
    # 暂时固定文件路径，后续初步打算修改为从 state 中传入
    pdf_path = "/root/program_projects/LangGraph/Resume_Data/sample/resume_sample_20200120/pdf/31b40b91486b.pdf"
    logging.info(f"嵌入简历文件: {pdf_path}")

    store_resume_to_vectorstore(pdf_path)
    return {}


def analyze_resume_structure(
        pdf_path: str,
        max_docs_num: int = 30,
) -> Dict[str, Any]:
    """
    使用 LLM 对整份简历进行结构化解析，提取出关键信息并组织成JSON格式，返回 Python dict。
    这里简单示例：只取前若干元素文本；你也可以改为只取前 N 页。
    """
    loader = UnstructuredPDFLoader(pdf_path, mode="elements")
    docs = loader.load()

    # 最多只取前 max_docs_num 个 chunk 输入 LLM 进行进一步的解析
    # 这是为了控制长度，避免 prompt 过大
    text = "\n\n".join(d.page_content for d in docs[:max_docs_num])

    # 用于后续LLM的系统提示词，指导其输出符合要求的JSON结构
    system_content = (
        "你是一个专业的简历解析助手，负责将中文或英文简历解析为结构化 JSON。"
        "请严格按以下 JSON 结构输出：\n"
        "{\n"
        '  \"name\": \"姓名字符串或 null\",\n'
        '  \"email\": \"邮箱或 null\",\n'
        '  \"phone\": \"手机或 null\",\n'
        '  \"education\": [\n'
        "    {\n"
        '      \"school\": \"学校\",\n'
        '      \"degree\": \"学位\",\n'
        '      \"major\": \"专业\",\n'
        '      \"start_date\": \"YYYY-MM 或 null\",\n'
        '      \"end_date\": \"YYYY-MM 或 null\"\n'
        "    }\n"
        "  ],\n"
        '  \"experiences\": [\n'
        "    {\n"
        '      \"company\": \"公司名称\",\n'
        '      \"title\": \"职位\",\n'
        '      \"start_date\": \"YYYY-MM 或 null\",\n'
        '      \"end_date\": \"YYYY-MM 或 null\",\n'
        '      \"description\": \"主要职责和成就，字符串\"\n"'
        "    }\n"
        "  ],\n"
        '  \"skills\": [\"技能1\", \"技能2\"]\n'
        "}\n"
        "必须是合法 JSON，不要额外说明文字。"
        "如果某个字段在简历中找不到，就填 null 或空列表。"
    )

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=f"下面是一份简历的文本内容，请解析：\n\n{text}"),
    ]

    resp = llm.invoke(messages)
    try:
        data = json.loads(resp.content)
    except json.JSONDecodeError:
        data = {"raw_output": resp.content}
    return data


def resume_structured_node(state: OverallState) -> dict:
    """
    一个可选节点：对指定 pdf_path 做结构化解析。
    如果需要的输出结果是将简历的关键信息提取并格式化，可以使用该方法创建一个结点
    这里暂时从 state.request 中约定传入路径，例如：解析: /path/to/resume.pdf
    后续可以修改成更可靠的参数传递方式。
    """
    request = state["request"].strip()
    # 这里简单做一个非常粗糙的解析，你可以改成更可靠的参数传递方式
    if request.startswith("解析:"):
        pdf_path = request.replace("解析:", "").strip()
    else:
        logging.warning("未在 request 中找到 pdf 路径，跳过结构化解析")
        return {}

    result = analyze_resume_structure(pdf_path)
    logging.info(f"结构化解析结果: {result}")
    # 结构化结果你可以在 OverallState 里加一个字段来存储，这里简单放到 rag_res
    return {
        "rag_res": {
            RESUME_AGENT_NAME: json.dumps(result, ensure_ascii=False)
        }
    }


def format_docs(docs: List[Document]) -> str:
    """
    将检索到的文档片段格式化为字符串，供生成节点使用。
    这里简单示例：每个片段前加上编号和来源信息。
    """
    return "\n\n".join(
        f"[片段{idx + 1}] 来源: {d.metadata.get('source', '')}\n内容：\n{d.page_content}"
        for idx, d in enumerate(docs)
    )


def resume_retrieve_node(state: OverallState) -> dict:
    """
    检索节点：基于 create_history_aware_retriever 进行多轮上下文检索。
    支持从 state.messages 中获取历史对话。
    """
    logging.info("--- 简历 RAG: 检索阶段 ---")
    user_input = state["request"]
    chat_history: List[BaseMessage] = state.get("messages", [])

    # 如果你要按 candidate_id 过滤，可以在这里基于 metadata 做二次过滤：
    # 目前示例直接使用 history_aware_retriever
    docs = history_aware_retriever.invoke({
        "input": user_input,
        "chat_history": chat_history,
    })

    logging.info(f"检索到 {len(docs)} 个文档片段")
    logging.info(f"检索结果：\n{format_docs(docs)}")
    return {
        "documents": {
            RESUME_AGENT_NAME: docs
        }
    }


def resume_generate_node(state: OverallState) -> dict:
    """
    生成节点：结合检索片段 + 对话历史 + 当前问题，调用 LLM 生成最终回答。
    """
    logging.info("--- 简历 RAG: 生成阶段 ---")
    user_input = state["request"]
    documents = state.get("documents", [])
    if documents is not []:
        documents = documents.get(RESUME_AGENT_NAME, [])
    history = state.get("messages", [])

    # 格式化检索到的文档片段，便于嵌入提示词模板
    examples = format_docs(documents)

    # 定义提示词模板
    template = (
        "你是一个专业的 HR 助理，只能基于提供的候选人简历内容回答问题，"
        "不要编造简历中不存在的信息；如果无法在简历中找到答案，就回答\"根据简历信息无法确定\"。\n\n"
        "【检索到的简历片段】:\n{examples}\n\n"
        "【当前问题】:\n{input}\n\n"
        "请基于上述片段作答，如有多个冲突信息请以最近时间为准。"
    )

    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template(template),
    ])

    # 构建 RAG 链
    rag_chain = prompt | llm | StrOutputParser()

    # 调用 RAG 链生成回答
    answer = rag_chain.invoke({
        "history": history,
        "examples": examples,
        "input": user_input,
    })

    logging.info(f"生成回答: {answer}")
    return {
        "rag_res": {
            RESUME_AGENT_NAME: answer
        }
    }
# 需要注意的是：结点函数的返回的状态只会更新子Graph的状态，而不会直接更新主Graph的状态，但是主Graph的调用依旧能够得到这些返回值
# 因此如果需要将子Graph的状态同步回到主Graph，就需要在主Graph中再返回调用的结果，也就是子Graph的输出


# --- 构建简历 RAG Agent 图 ---

async def create_resume_agent_graph():
    """
    创建并编译用于简历 RAG 的 StateGraph。这相当于主Graph下的一个子Graph，专门用于处理简历分析任务。
    这里给出一个最简单的两步流程：retrieve -> generate。
    如果你需要结构化解析，可在 supervisor 图中单独接入 resume_structured_node。
    """
    graph_builder = StateGraph(OverallState)

    # 添加节点
    graph_builder.add_node("resume_retrieve", resume_retrieve_node)
    graph_builder.add_node("resume_generate", resume_generate_node)
    # 可选结构化节点（不在主链路上）
    graph_builder.add_node("resume_structured", resume_structured_node)

    # 主链路: 入口 -> 检索 -> 生成 -> END
    graph_builder.set_entry_point("resume_retrieve")
    graph_builder.add_edge("resume_retrieve", "resume_generate")
    graph_builder.add_edge("resume_generate", END)

    # 编译图，复用全局的 checkpointer
    checkpointer = await utils.get_checkpointer()
    resume_agent = graph_builder.compile(checkpointer=checkpointer)
    return resume_agent


# 对外暴露懒加载的简历 Agent
resume_agent = None


async def get_resume_agent():
    global resume_agent
    if resume_agent is None:
        resume_agent = await create_resume_agent_graph()
    return resume_agent


# 简单测试入口
if __name__ == "__main__":
    import asyncio


    async def main():
        need_embed = input("是否需要重新嵌入简历文档？(y/n): ")
        if need_embed.lower() == 'y':
            # 1. 先把一份简历写入向量库（实际项目中应在上传环节做）
            pdf_path = "/root/program_projects/LangGraph/Resume_Data/sample/resume_sample_20200120/pdf/31b40b91486b.pdf"
            store_resume_to_vectorstore(pdf_path, candidate_id="candidate_001")

        # 2. 获取 agent
        agent = await get_resume_agent()

        # 3. 测试多轮对话
        inputs = {"request": "这位候选人的最高学历是什么？"}

        async for output in agent.astream(
                inputs,
                config=utils.resume_config,
        ):
            for node, value in output.items():
                print(f"--- Node: {node} ---")
                print(value)
                print("\n")


    asyncio.run(main())
