import asyncio
import json
import logging
import os
import sys

import redis
from langchain_chroma import Chroma
from langchain_core.runnables import RunnableConfig
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from psycopg_pool import AsyncConnectionPool, ConnectionPool

"""
全局配置文件，定义了日志配置、API Key、记忆存储配置等全局使用的内容。
"""
# workspace_root = "/root/program_projects/ResumeSystem/"
# settings_file = open(workspace_root + "ResumeAnalyse/settings.json", "r", encoding="utf-8")
# settings = json.load(settings_file)     # 加载全局配置文件内容

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

# 内存实现的短期和长期记忆
# checkpointer = InMemorySaver()
# store = InMemoryStore()


pg_host = settings["PostgreSql"]["Host"]
pg_port = settings["PostgreSql"]["Port"]
pg_db = settings["PostgreSql"]["Database"]
pg_username = settings["PostgreSql"]["Username"]
pg_password = settings["PostgreSql"]["Password"]
# 以下是基于PostgreSQL数据库实现的短期和长期记忆，会将记忆内容记录到PostgreSQL的langgraph database中
PG_DB_URL = f"postgresql://{pg_username}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

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
store: AsyncPostgresSaver = None
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
        # checkpointer_cm = AsyncPostgresSaver.from_conn_string(str(PG_DB_URL))
        # checkpointer = await checkpointer_cm.__aenter__()
        checkpointer = await AsyncPostgresSaver.from_conn_string(str(PG_DB_URL))
    return checkpointer


async def get_store():
    global store
    if store is None:
        # 由于Graph中涉及到异步调用（MCP服务），因此这里使用异步版本的PostgreSQL实现的短期和长期记忆
        # store_cm = AsyncPostgresStore.from_conn_string(str(PG_DB_URL))
        # store = await store_cm.__aenter__()
        store = await AsyncPostgresStore.from_conn_string(str(PG_DB_URL))
    return store


"""
获取基于连接池的异步checkpointer和store
更推荐使用这种方式，以提高并发性能
"""
async def get_pooled_checkpointer():
    """获取基于连接池的checkpointer"""
    global checkpointer, checkpointer_connection_pool
    if checkpointer is None:
        # 创建连接池
        checkpointer_connection_pool = AsyncConnectionPool(conninfo=str(PG_DB_URL), max_size=20)
        # 开启连接池
        await checkpointer_connection_pool.open()
        # 由于Graph中涉及到异步调用（MCP服务），因此这里使用异步版本的PostgreSQL实现的短期和长期记忆
        checkpointer = AsyncPostgresSaver(conn=checkpointer_connection_pool)
    return checkpointer


async def get_pooled_store():
    """获取基于连接池的store"""
    global store, store_connection_pool
    if store is None:
        # 创建连接池
        store_connection_pool = AsyncConnectionPool(conninfo=str(PG_DB_URL), max_size=10)
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
    checkpointer = await get_checkpointer()
    store = await get_store()
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


async def delete_memory_by_thread_id(thread_id: str):
    """根据thread_id删除相关的记忆数据"""
    if checkpointer is not None:
        await checkpointer.adelete_thread(thread_id)
    if store is not None:
        await store.adelete_thread(thread_id)
    logging.info(f"已删除 thread_id={thread_id} 相关的记忆数据")


async def get_checkpointer_memory(config: RunnableConfig):
    """获取特定的checkpointer内的数据"""
    checkpoint = None
    if checkpointer is not None:
        checkpoint = await checkpointer.aget_tuple(config)
    if checkpoint is not None:
        logging.debug(f"已获取 checkpoint: {checkpoint}")
    else:
        logging.debug(f"未找到对应的 checkpoint，config: {config}")
    return checkpoint


async def get_store_memory(config: RunnableConfig):
    """获取特定的store内存储的数据"""
    stored_data = None
    if store is not None:
        stored_data = await store.aget_tuple(config)
    if stored_data is not None:
        logging.debug(f"已获取 store 数据: {stored_data}")
    else:
        logging.debug(f"未找到对应的 store 数据，config: {config}")
    return stored_data


redis_host = settings["Redis"]["Host"]
redis_port = settings["Redis"]["Port"]
redis_db = settings["Redis"]["Database"]
redis_password = settings["Redis"]["Password"]
redis_decode_responses = settings["Redis"]["Decode_Responses"]
redis_pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=redis_db, decode_responses=redis_decode_responses,
                                  password=redis_password)
redis_client = redis.Redis(connection_pool=redis_pool)


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
    asyncio.run(setup_memory())
