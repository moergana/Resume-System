PDF_FILE_SUFFIX = ".pdf"
DOC_FILE_SUFFIX = ".doc"
DOCX_FILE_SUFFIX = ".docx"
PPT_FILE_SUFFIX = ".ppt"
PPTX_FILE_SUFFIX = ".pptx"
IMAGE_FILE_SUFFIX_LIST = [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]

# 简历分析状态常量
RESUME_ANALYSIS_WAITING_STATUS = 0
RESUME_ANALYSIS_ANALYSING_STATUS = 1
RESUME_ANALYSIS_FINISHED_STATUS = 2
RESUME_ANALYSIS_FAILED_STATUS = 3

# 消息队列传来的请求类型常量
REQUEST_RESUME_UPLOAD = "resume_upload"
REQUEST_JD_UPLOAD = "jd_upload"
REQUEST_RESUME_JD_DIFFER = "resume_jd_differ"
REQUEST_RESUME_ADVISE = "resume_advise"
REQUEST_JD_MATCH = "jd_match"
REQUEST_RESUME_MATCH = "resume_match"
REQUEST_RESUME_DELETE = "resume_delete"
REQUEST_JD_DELETE = "jd_delete"

# 用于保存分析记录详细信息到Redis的Redis Key前缀
RESUME_ANALYSIS_REDIS_KEY_PREFIX = "resume_analysis:chatbot_context:"
RESUME_ANALYSIS_REDIS_TTL = 1 * 60 * 60  # 1小时，单位为秒
NULL_REDIS_TTL = 3 * 60  # 3分钟，单位为秒
# resume analysis的布谷鸟过滤器的Redis Key
RESUME_ANALYSIS_CUCKOO_FILTER_REDIS_KEY = "cuckoo_filter:resume_analysis"

# 聊天机器人（Conversation.py）相关常量
CONVERSATION_MAX_TOKENS = 20000     # 触发上下文总结压缩的最大历史对话Token数
CONVERSATION_MAX_DIALOGUES = 8      # 触发上下文总结压缩的最大历史对话轮数


def get_resume_analysis_redis_key(analysis_id: int) -> str:
    """
    获取简历分析在Redis中的Key
    :param analysis_id: 分析记录ID
    :return: Redis Key
    """
    return f"{RESUME_ANALYSIS_REDIS_KEY_PREFIX}{analysis_id}"

# 检索算法名称常量
SIMILARITY_FUNCTION = "similarity"  # 基于向量相似度的检索方法
MMR_FUNCTION = "mmr"  # 基于最大边际相关性的检索
SIMILARITY_BM25_FUNCTION = "similarity_bm25"  # 基于向量相似度和BM25文本匹配的混合检索方法

# 重排算法参数常量，用于混合检索中不同检索结果的融合
RRF_K = 100  # Reciprocal Rank Fusion算法中的k值，该值越大，某一个排名对最终得分的影响会越小，得分的上限也会越小
