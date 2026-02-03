import logging

import aio_pika

from ResumeAnalyse.utils import settings
from pika.connection import ConnectionParameters
from pika.credentials import PlainCredentials

from ResumeAnalyse.entity.resume_analysis_dto import ResumeAnalysisDTO

# 配置日志记录。
# 如果需要debug，就将level参数改为logging.DEBUG。默认level为logging.INFO。
logging.basicConfig(
    level=logging.INFO
)

# 从配置文件中获取RabbitMQ的连接设置
rabbitmq_settings = settings.get("RabbitMQ", {})

# 创建pika依赖的RabbitMQ连接参数，只能用于同步的pika
mq_parameters = ConnectionParameters(
    host=rabbitmq_settings.get("Host", "localhost"),
    port=rabbitmq_settings.get("Port", 5672),
    virtual_host=rabbitmq_settings.get("Virtual_Host", "/"),
    credentials=PlainCredentials(
        username=rabbitmq_settings.get("Username", ""),
        password=rabbitmq_settings.get("Password", "")
    )
)

aio_mq_parameters = {
    "host": rabbitmq_settings.get("Host", "localhost"),
    "port": rabbitmq_settings.get("Port", 5672),
    "virtualhost": rabbitmq_settings.get("Virtual_Host", "/"),
    "login": rabbitmq_settings.get("Username", ""),
    "password": rabbitmq_settings.get("Password", "")
}


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
