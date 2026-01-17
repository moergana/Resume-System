import contextvars

# 使用contextvars来保存当前线程内需要全局共享的数据

thread_conversation_agent = contextvars.ContextVar("conversation_agent", default=None)
thread_conversation_config = contextvars.ContextVar("conversation_config", default=None)

thread_resume_summary_text = contextvars.ContextVar("resume_summary_text", default="")
thread_jd_summary_text = contextvars.ContextVar("jd_summary_text", default="")
thread_match_score = contextvars.ContextVar("match_score", default=0)
thread_resume_advice = contextvars.ContextVar("resume_advice", default="")
thread_job_hunting_advice = contextvars.ContextVar("job_hunting_advice", default="")
