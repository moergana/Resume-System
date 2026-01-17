import logging

from pika.connection import ConnectionParameters
from pika.credentials import PlainCredentials

from ResumeAnalyse.entity.resume_analysis_dto import ResumeAnalysisDTO

# 配置日志记录。
# 如果需要debug，就将level参数改为logging.DEBUG。默认level为logging.INFO。
logging.basicConfig(
    level=logging.INFO
)

mq_parameters = ConnectionParameters(
    host="localhost",
    port=5672,
    virtual_host="/resumesys",
    credentials=PlainCredentials(
        username="resumesys",
        password="resume123"
    )
)


def generate_jd_summary_text(request: ResumeAnalysisDTO):
    """
    根据 ResumeAnalysisDTO 类型的 request 中的title、company、location等信息生成JD摘要文本
    :param request:
    :return:
    """
    summary = f"""职位标题: {request.title}
公司名称: {request.company}
工作地点: {request.location}
薪资: {request.salary}
职位描述: {request.description}
职位要求: {request.requirements}
职位福利: {request.bonus}
"""
    return summary
