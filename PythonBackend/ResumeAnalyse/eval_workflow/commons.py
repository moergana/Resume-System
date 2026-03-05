import json
import logging
import os
import sys

import redis
from sqlalchemy import create_engine


"""
全局配置文件，定义了日志配置、API Key、记忆存储配置等全局使用的内容。
"""
# 使用相对路径，兼容打包后的环境，方便部署到各种目录下
# 首先获取当前模块所在的绝对路径：
# __file__ 是一个特殊变量，表示当前脚本的路径；os.path.abspath(__file__) 获取当前脚本的绝对路径；os.path.dirname() 获取该路径的目录部分

current_dir = os.path.dirname(os.path.abspath(__file__))
# workspace_root 就是 current_dir
workspace_root = current_dir
# settings.json 位于当前模块同级目录
settings_file_path = os.path.join(current_dir, "settings.json")

# 如果在打包环境中，资源文件可能被解压到临时目录，或者都在 _internal 中
# PyInstaller 设置了 sys._MEIPASS
if hasattr(sys, '_MEIPASS'):
    settings_file_path = os.path.join(sys._MEIPASS, 'ResumeAnalyse', 'eval_workflow', 'settings.json')
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

openrouter_api_key_2 = os.getenv("OPENROUTER_KEY_2")
assert openrouter_api_key_2, "请先在系统环境变量中设置 OPENROUTER_KEY_2！"
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