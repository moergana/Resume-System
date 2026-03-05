import asyncio
import json
import logging
import os
import sys

from langchain_milvus import BM25BuiltInFunction, Milvus
from rdflib import collection
import redis
from langchain_chroma import Chroma
from langchain_core.runnables import RunnableConfig
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from psycopg_pool import AsyncConnectionPool, ConnectionPool
from sqlalchemy import create_engine

from ResumeAnalyse.constants import DOC_FILE_SUFFIX, DOCX_FILE_SUFFIX, IMAGE_FILE_SUFFIX_LIST, PDF_FILE_SUFFIX, PPT_FILE_SUFFIX, PPTX_FILE_SUFFIX

"""
全局配置文件，定义了日志配置、API Key、记忆存储配置等全局使用的内容。
"""
# 使用相对路径，兼容打包后的环境，方便部署到各种目录下
# 首先获取当前模块所在的绝对路径：
# __file__ 是一个特殊变量，表示当前脚本的路径；os.path.abspath(__file__) 获取当前脚本的绝对路径；os.path.dirname() 获取该路径的目录部分
current_dir = os.path.dirname(os.path.abspath(__file__))
# 假设 workspace_root 是 ResumeAnalyse 的上一级目录
workspace_root = os.path.dirname(current_dir)
# settings.json 位于当前模块同级目录
settings_file_path = os.path.join(current_dir, "settings.json")

# 如果在打包环境中，资源文件可能被解压到临时目录，或者都在 _internal 中
# PyInstaller 设置了 sys._MEIPASS
if hasattr(sys, '_MEIPASS'):
    settings_file_path = os.path.join(sys._MEIPASS, 'ResumeAnalyse', 'settings.json')
    # 如果找不到，尝试直接在根目录
    if not os.path.exists(settings_file_path):
        settings_file_path = os.path.join(sys._MEIPASS, 'settings.json')

if os.path.exists(settings_file_path):
    settings_file = open(settings_file_path, "r", encoding="utf-8")
    settings = json.load(settings_file)     # 加载全局配置文件内容
else:
    # Fallback or error handling
    logging.warning(f"Settings file not found at {settings_file_path}")
    settings = {}


# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为INFO，即记录INFO及以上级别的日志
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 设置日志格式，包含时间、模块名、日志级别和消息内容
)

# LLM API Key 配置
# Google Gemini API Key
gemini_api_key = os.getenv("GEMINI_API_KEY")
assert gemini_api_key, "请先在系统环境变量中设置 GEMINI_API_KEY！"
""" 
# Google 官方 Gemini API 调用
llm = init_chat_model(
    model="gemini-2.5-flash",
    model_provider="google_genai",
    api_key=utils.api_key,
) 
"""

# OpenRouter 平台 API Key
openrouter_api_key = os.getenv("OPENROUTER_KEY")
assert openrouter_api_key, "请先在系统环境变量中设置 OPENROUTER_KEY！"
""" 
# OpenRouter 平台模型调用
Model_Name = "z-ai/glm-4.5-air:free"
Base_URL = "https://openrouter.ai/api/v1"
llm = init_chat_model(
    model=Model_Name,
    base_url=Base_URL,
    model_provider="openai",
    api_key=utils.openrouter_api_key,
)
"""

# 智谱（Big Model） API Key
# big_model_api_key = os.getenv("BIG_MODEL_API_KEY")
# assert big_model_api_key, "请先在系统环境变量中设置 BIG_MODEL_API_KEY！"
""" 
# 智谱（Big Model）平台模型调用
llm = ChatZhipuAI(
    model="glm-4.5-flash",
    api_key=utils.big_model_api_key,
    temperature=0.5,
) 
"""

# Dashscope API Key 配置
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
assert dashscope_api_key, "请先在系统环境变量中设置 DASHSCOPE_API_KEY！"


# Tavily API Key 配置
tavily_api_key = os.getenv("TAVILY_API_KEY")
assert tavily_api_key, "请先在系统环境变量中设置 TAVILY_API_KEY！"


"""
MySQL数据库配置
"""
mysql_host = settings["MySQL"]["Host"]
mysql_port = settings["MySQL"]["Port"]
mysql_db = settings["MySQL"]["Database"]
mysql_username = settings["MySQL"]["Username"]
mysql_password = settings["MySQL"]["Password"]
# 该URL适用于SQLAlchemy创建数据库引擎
MYSQL_DB_URL = f"mysql+pymysql://{mysql_username}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}?charset=utf8mb4"
# 创建一个全局可用的SQLAlchemy引擎实例
mysql_engine = create_engine(
    url=MYSQL_DB_URL,
    pool_size=10,         # 连接池大小，连接池常驻的核心连接数量
    max_overflow=20,      # 连接池最大溢出数量，当池满了之后，允许临时额外创建的连接数
    pool_timeout=30,      # 连接池获取连接的超时时间
    pool_recycle=14400,    # 连接池中连接的回收周期，多久之后强制回收连接（MySQL默认8小时自动断开无活动的连接，导致连接失效）。单位秒
    pool_pre_ping=True    # 启用连接池预检功能，每次取连接前先“ping”一下，确保连接还活着
)


"""
Redis配置
"""
redis_host = settings["Redis"]["Host"]
redis_port = settings["Redis"]["Port"]
redis_db = settings["Redis"]["Database"]
redis_password = settings["Redis"]["Password"]
redis_decode_responses = settings["Redis"]["Decode_Responses"]
redis_pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=redis_db, decode_responses=redis_decode_responses,
                                  password=redis_password)
redis_client = redis.Redis(connection_pool=redis_pool)


"""
嵌入模型配置
"""
# example: embed_model_name = "Qwen/Qwen3-Embedding-0.6B"
embed_model_name = settings["Model"]["Embed_Model_Name"]
embed_model = HuggingFaceEmbeddings(model_name=embed_model_name)

resume_collection_name = "resume_collection"
# resume_collection_persist_directory = workspace_root + "ResumeAnalyse/chroma_data/resumes"
resume_collection_persist_directory = os.path.join(workspace_root, "ResumeAnalyse", "chroma_data", "resumes")

JD_collection_name = "JD_collection"
# JD_collection_persist_directory = workspace_root + "ResumeAnalyse/chroma_data/JDs"
JD_collection_persist_directory = os.path.join(workspace_root, "ResumeAnalyse", "chroma_data", "JDs")
""" 
# 初始化Chroma向量数据库实例
resume_vectordb = Chroma(
    collection_name=resume_collection_name,
    embedding_function=embed_model,
    persist_directory=resume_collection_persist_directory,
)

JD_vectordb = Chroma(
    collection_name=JD_collection_name,
    embedding_function=embed_model,
    persist_directory=JD_collection_persist_directory,
)
"""

# 初始化Milvus向量数据库实例
# Milvus相比于Chroma，具有更高的性能和可扩展性，适合处理大规模的向量数据和高并发的查询请求。
# 首先，定义Milvus向量数据库的collection在本地保存的文件路径（这和Chroma使用一个目录是不同的）
milvus_collection_dir = os.path.join(workspace_root, "milvus_data")
if not os.path.exists(milvus_collection_dir):
    os.makedirs(milvus_collection_dir)
    logging.info(f"Created directory for Milvus collections at {milvus_collection_dir}.")
resume_collection_db_file = os.path.join(workspace_root, "ResumeAnalyse", "milvus_data", "resumes_collection.db")
JD_collection_db_file = os.path.join(workspace_root, "ResumeAnalyse", "milvus_data", "JDs_collection.db")

# 定义Milvus向量数据库实例，指定embedding_function、collection_name和connection_args等参数
resume_vectordb = Milvus(
    embedding_function=embed_model,
    collection_name=resume_collection_name,  # 指定 collection 名称
    connection_args={
        "uri": resume_collection_db_file,  # collection保存的文件路径
    },
    # 混合检索必需的配置
    builtin_function=BM25BuiltInFunction(),
    vector_field=["dense", "sparse"],
    index_params=[
        {"metric_type": "COSINE", "index_type": "FLAT"},
        {"metric_type": "BM25", "index_type": "SPARSE_INVERTED_INDEX", "params": {"drop_ratio_build": 0.2}}
    ],
    auto_id=False,   # 禁用自动生成ID，需要在添加文档时手动指定ID，且ID必须是字符串类型。
    drop_old=False,  # 如果已存在同名 collection 则删除重建。如果是生产环境想复用，设为 False
)

JD_vectordb = Milvus(
    embedding_function=embed_model,
    collection_name=JD_collection_name,  # 指定 collection 名称
    connection_args={
        "uri": JD_collection_db_file,  # collection保存的文件路径
    },
    # 混合检索必需的配置
    builtin_function=BM25BuiltInFunction(),
    vector_field=["dense", "sparse"],
    index_params=[
        {"metric_type": "COSINE", "index_type": "FLAT"},
        {"metric_type": "BM25", "index_type": "SPARSE_INVERTED_INDEX", "params": {"drop_ratio_build": 0.2}}
    ],
    auto_id=False,   # 禁用自动生成ID，需要在添加文档时手动指定ID，且ID必须是字符串类型。
    drop_old=False,  # 如果已存在同名 collection 则删除重建。如果是生产环境想复用，设为 False
)


"""
PostgreSQL数据库配置
"""
pg_host = settings["PostgreSQL"]["Host"]
pg_port = settings["PostgreSQL"]["Port"]
pg_db = settings["PostgreSQL"]["Database"]
pg_username = settings["PostgreSQL"]["Username"]
pg_password = settings["PostgreSQL"]["Password"]
# 以下是基于PostgreSQL数据库实现的短期和长期记忆，会将记忆内容记录到PostgreSQL的langgraph database中
PG_DB_URL = f"postgresql://{pg_username}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"


# ----------------------------------------------------------------
# 以下是关于记忆机制的配置和工具函数，以及一些与记忆相关的全局变量和函数。
# ----------------------------------------------------------------

# 内存实现的短期和长期记忆
# checkpointer = InMemorySaver()
# store = InMemoryStore()

# from_conn_string() 方法返回的是一个上下文管理器
# 如果使用with调用则直接能获取到checkpointer和store对象

# checkpointer_cm = PostgresSaver.from_conn_string(str(DB_URL))
# store_cm = PostgresStore.from_conn_string(str(DB_URL))

# 这里使用 __enter__() 方法来获取上下文管理器中的checkpointer和store对象
# checkpointer = checkpointer_cm.__enter__()
# store = store_cm.__enter__()


# 接下来通过异步函数，使用异步上下文管理器获取checkpointer和store对象
# 这里使用 __aenter__() 方法来获取异步上下文管理器中的checkpointer和store对象
# 并且采用懒加载的方式，只有在需要时才创建对象
checkpointer: AsyncPostgresSaver = None
store: AsyncPostgresStore = None
sync_checkpointer: PostgresSaver = None     # 同步版本的checkpointer
sync_store: PostgresSaver = None           # 同步版本的store

# 为checkpointer和store创建异步连接池，以提高并发性能
checkpointer_connection_pool: AsyncConnectionPool = None
store_connection_pool: AsyncConnectionPool = None
checkpointer_sync_connection_pool: ConnectionPool = None    # 同步版本的连接池
store_sync_connection_pool: ConnectionPool = None        # 同步版本的连接池


async def get_checkpointer():
    global checkpointer
    if checkpointer is None:
        # 由于Graph中涉及到异步调用（MCP服务），因此这里使用异步版本的PostgreSQL实现的短期和长期记忆
        checkpointer_cm = AsyncPostgresSaver.from_conn_string(str(PG_DB_URL))
        checkpointer = await checkpointer_cm.__aenter__()
    return checkpointer


async def get_store():
    global store
    if store is None:
        # 由于Graph中涉及到异步调用（MCP服务），因此这里使用异步版本的PostgreSQL实现的短期和长期记忆
        store_cm = AsyncPostgresStore.from_conn_string(str(PG_DB_URL))
        store = await store_cm.__aenter__()
    return store


"""
获取基于连接池的异步checkpointer和store
更推荐使用这种方式，以提高并发性能
"""
async def get_pooled_checkpointer():
    """获取基于连接池的checkpointer"""
    global checkpointer, checkpointer_connection_pool
    if checkpointer is None:
        # 创建连接池(将open参数设为False，该参数已被废弃)
        checkpointer_connection_pool = AsyncConnectionPool(conninfo=str(PG_DB_URL), max_size=20, open=False)
        # 开启连接池
        await checkpointer_connection_pool.open()
        # 由于Graph中涉及到异步调用（MCP服务），因此这里使用异步版本的PostgreSQL实现的短期和长期记忆
        checkpointer = AsyncPostgresSaver(conn=checkpointer_connection_pool)
    return checkpointer


async def get_pooled_store():
    """获取基于连接池的store"""
    global store, store_connection_pool
    if store is None:
        # 创建连接池(将open参数设为False，该参数已被废弃)
        store_connection_pool = AsyncConnectionPool(conninfo=str(PG_DB_URL), max_size=10, open=False)
        # 开启连接池
        await store_connection_pool.open()
        # 由于Graph中涉及到异步调用（MCP服务），因此这里使用异步版本的PostgreSQL实现的短期和长期记忆
        store = AsyncPostgresStore(conn=store_connection_pool)
    return store


"""
获取基于连接池的同步checkpointer和store
不同于上面的异步版本，同步版本用于同步代码读写Memory数据库
"""
def get_sync_pooled_checkpointer():
    """获取基于连接池的同步checkpointer"""
    global sync_checkpointer, checkpointer_sync_connection_pool
    if sync_checkpointer is None:
        # 创建连接池
        checkpointer_sync_connection_pool = ConnectionPool(conninfo=str(PG_DB_URL), max_size=20)
        # 由于Graph中涉及到异步调用（MCP服务），因此这里使用异步版本的PostgreSQL实现的短期和长期记忆
        sync_checkpointer = PostgresSaver(conn=checkpointer_sync_connection_pool)
    return sync_checkpointer


def get_sync_pooled_store():
    """获取基于连接池的同步store"""
    global sync_store, store_sync_connection_pool
    if sync_store is None:
        # 创建连接池
        store_sync_connection_pool = ConnectionPool(conninfo=str(PG_DB_URL), max_size=10)
        # 由于Graph中涉及到异步调用（MCP服务），因此这里使用异步版本的PostgreSQL实现的短期和长期记忆
        sync_store = PostgresSaver(conn=store_sync_connection_pool)
    return sync_store


async def setup_memory():
    """
    这个方法用于初始化PostgreSQL数据库中的表结构。
    仅在第一次使用数据库时调用，后续不需要重复调用，以免删除已有的数据。
    """
    global checkpointer, store
    checkpointer = await get_pooled_checkpointer()
    store = await get_pooled_store()
    # 调用setup()方法初始化数据库表结构。
    # 需要注意，每次调用setup()，都会重置回到初始状态，删除所有已有的数据
    await checkpointer.setup()
    await store.setup()
    logging.info("AsyncPostgresSaver和AsyncPostgresStore记忆数据库初始化完成")


# 定义记忆退出函数，用于在Graph停止工作后断开数据库连接，释放资源
async def close_memory_connection():
    """异步清理函数，在程序退出时关闭连接"""
    # 检查对象是否已被创建，如果被创建了才调用退出
    if checkpointer is not None:
        # await checkpointer_cm.__aexit__(None, None, None)
        await checkpointer_connection_pool.close()
    if store is not None:
        # await store_cm.__aexit__(None, None, None)
        await store_connection_pool.close()


async def delete_checkpointer(config: RunnableConfig):
    """根据thread_id删除相关的记忆数据"""
    global checkpointer
    # 获取store对象
    checkpointer = await get_pooled_checkpointer()
    thread_id = config.get("configurable", {}).get("thread_id", "")
    # 删除thread_id相关的数据
    await checkpointer.adelete_thread(thread_id)
    logging.info(f"已删除 thread_id={thread_id} 相关的Checkpointer记忆数据")


async def delete_store(config: RunnableConfig):
    """根据thread_id删除相关的记忆数据"""
    global store
    # 获取checkpointer和store对象
    store = await get_pooled_store()
    store_namespace = config.get("configurable", {}).get("store_namespace", ())
    store_key = config.get("configurable", {}).get("store_key", "")
    # 删除store中相关的数据，需要指定Namespace和Key（而不是thread_id）
    await store.adelete(store_namespace, store_key)
    logging.info(f"已删除 namespace={store_namespace}, key={store_key} 相关的Store记忆数据")


async def get_checkpointer_memory(config: RunnableConfig):
    """获取特定的checkpointer内的数据"""
    global checkpointer, store
    # 获取checkpointer对象
    checkpointer = await get_pooled_checkpointer()
    # 获取记忆数据
    checkpoint = await checkpointer.aget(config)
    if checkpoint is not None:
        logging.info(f"已获取 checkpoint: {checkpoint}")
    else:
        logging.info(f"未找到对应的 checkpoint，config: {config}")
    return checkpoint


async def get_store_memory(config: RunnableConfig):
    """获取特定的store内存储的数据"""
    global checkpointer, store
    # 获取store对象
    store = await get_pooled_store()
    # 获取记忆数据
    # 首先需要从config中获取store_namespace和store_key
    store_namespace = config.get("configurable", {}).get("store_namespace")
    store_key = config.get("configurable", {}).get("store_key")
    stored_data = await store.aget(store_namespace, store_key)
        
    if stored_data:
        logging.debug(f"已获取 store 数据: {stored_data}")
    else:
        logging.debug(f"未找到对应的 store 数据，config: {config}")
    return stored_data


# Extractor.extract_file_to_markdown 方法支持处理的文件类型
support_file_types = [
    # PDF
    PDF_FILE_SUFFIX,
    # DOC
    DOC_FILE_SUFFIX,
    # DOCX
    DOCX_FILE_SUFFIX,
    # PPT
    PPT_FILE_SUFFIX,
    # PPTX
    PPTX_FILE_SUFFIX,
    # 图片
    *IMAGE_FILE_SUFFIX_LIST
]


"""
各结点的调用参数配置
thread_id: 用于区分不同会话上下文的ID
checkpoint_ns: 用于在同一thread_id的记忆内，进一步划分上下文的命名空间标识
               比如以下用法是将所有结点的记忆都放在同一个thread_id下，但通过不同的checkpoint_ns来区分各结点的各自的调用记忆
               因为不是每个结点都能在每次对话中被调用，所以不同结点产生的对话记录实际上是不同的，这里就通过checkpoint_ns来区分
               而全局的对话上下文则通过state来记录，并同步给所有的结点。而由于所有agent整体是一个系统，所以它们应该使用同一个thread_id
               
thread_id = "test2"  # 多Agent图的线程ID，用于区分不同的对话上下文
agent_config = {
    "configurable": {
        "thread_id": thread_id,
        "checkpoint_ns": "supervisor",
    },
}
"""

# thread_local = threading.local()    # 线程本地存储，可用于存储当前线程中共享的数据
# threading.local() 使用 contextvars 替代，以支持异步环境下的上下文管理


if __name__ == "__main__":
    command_id = input(f"""
请输入要执行的命令编号：
"0": 查看命令列表
"1": 初始化基于PostgreSQL的 checkpointer 和 store 的数据库表结构
"2": 删除指定thread_id的checkpointer的数据
"3": 删除指定namespace和key的store的数据
"4": 查询指定thread_id的checkpointer的数据
"5": 查询指定namespace和key的store的数据
"quit" or "exit": 退出（不执行任何命令）
您的选择是：""")
    try:
        while True:
            if command_id == "0":
                print("""命令编号：
"0": 查看命令列表
"1": 初始化基于PostgreSQL的 checkpointer 和 store 的数据库表结构
"2": 删除指定thread_id的checkpointer的数据
"3": 删除指定namespace和key的store的数据
"4": 查询指定thread_id的checkpointer的数据
"5": 查询指定namespace和key的store的数据
"quit" or "exit": 退出（不执行任何命令）""")

            elif command_id == "1":
                print("正在初始化基于PostgreSQL的 checkpointer 和 store 的数据库表结构...")
                asyncio.run(setup_memory())
                print("初始化完成！")

            elif command_id == "2":
                thread_id = input("请输入要删除的checkpointer的记录对应的 thread_id：")
                print(f"正在删除 thread_id={thread_id} 相关的记忆数据...")
                config_dict = {
                    "configurable": {
                        "thread_id": str(thread_id),
                    },
                }
                asyncio.run(delete_checkpointer(config_dict))
                print("删除完成！")

            elif command_id == "3":
                store_namespace = input("请输入要删除的store的记录对应的 namespace（多个namespace用逗号分隔）：")
                store_key = input("请输入要删除的store的记录对应的 key：")
                print(f"正在删除 namespace={store_namespace}, key={store_key} 相关的记忆数据...")
                config_dict = {
                    "configurable": {
                        "store_namespace": tuple(store_namespace.split(",")),
                        "store_key": str(store_key),
                    },
                }
                asyncio.run(delete_store(RunnableConfig(**config_dict)))
                print("删除完成！")

            elif command_id == "4":
                thread_id = input("请输入要查询记忆数据的 thread_id：")
                print(f"正在查询 thread_id={thread_id} 相关的记忆数据...")
                config_dict = {
                    "configurable": {
                        "thread_id": str(thread_id)
                    },
                }
                asyncio.run(get_checkpointer_memory(RunnableConfig(**config_dict)))

            elif command_id == "5":
                store_namespace = input("请输入要查询记忆数据的 namespace（多个namespace用逗号分隔）：")
                store_key = input("请输入要查询记忆数据的 key：")
                print(f"正在查询 namespace={store_namespace}, key={store_key} 相关的记忆数据...")
                config_dict = {
                    "configurable": {
                        "store_namespace": tuple(store_namespace.split(",")),
                        "store_key": str(store_key),
                    },
                }
                asyncio.run(get_store_memory(RunnableConfig(**config_dict)))

            elif command_id.lower() == "quit" or command_id.lower() == "exit":
                print("退出程序，不执行任何命令。")
                break
            else:
                print("无效的命令编号，请重新输入有效的编号！")

            command_id = input("请继续输入要执行的命令编号，或输入 'quit' 或 'exit' 退出：")

    except Exception as e:
        print(f"执行命令时发生异常：{e}")
        raise e
