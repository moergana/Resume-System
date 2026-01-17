# 整个Graph的全局状态
from operator import add
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # 聊天消息列表

    user_id: str  # 用户的唯一标识

    request_type: str  # 用户的请求的类型

    resume_path: str  # 上传的简历文件访问路径
    jd_path: str  # 上传的JD文件访问路径
    resume_id: str  # 简历在向量数据库中的唯一标识
    jd_id: str  # JD在向量数据库中的唯一标识
    resume_summary_text: str  # 简历摘要信息
    jd_summary_text: str  # 职位描述摘要信息

    match_score: int  # 简历与职位描述的匹配度分数
    differences: str  # 简历与JD的差异点（面向招聘者）
    improvement_suggestions: str    # 针对简历的改进建议（面向求职者）
    job_hunting_tips: str  # 针对求职的建议（面向求职者）

    retrieved_resumes: Annotated[List[dict], add]  # 检索到的相关简历列表
    retrieved_jds: Annotated[List[dict], add]  # 检索到的相关JD列表

    state: str  # 当前Graph的执行状态
    log_msg: Annotated[List[str], add]    # 执行过程中的日志信息
