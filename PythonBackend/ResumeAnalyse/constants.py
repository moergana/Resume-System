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
RESUME_ANALYSIS_REDIS_TTL = 7 * 24 * 60 * 60  # 7天，单位为秒

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
