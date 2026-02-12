import logging

from pika.channel import Channel
from pika.spec import Basic, BasicProperties
import ResumeAnalyse.rabbitmq.utils
from ResumeAnalyse.Vectorizer import resume_vectordb, JD_vectordb
from ResumeAnalyse.entity.resume_analysis_dto import ResumeAnalysisDTO


def resume_delete_callback(ch: Channel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
    """
    Callback function to handle resume delete requests from RabbitMQ.
    :param ch: Channel
    :param method: Method
    :param properties: Properties
    :param body: Message body
    """
    resume_id = None
    delivery_tag = method.delivery_tag
    try:
        print(" [x] Received resume delete request:", body)
        # 在这里添加处理简历删除请求的逻辑
        # 例如，从数据库中删除简历记录，清理相关资源等
        print(" [x] Resume delete request processed")
        # 首先将body转换为字符串
        body_str = body.decode('utf-8')
        logging.info(f"接收到来自queue: RESUME_DELETE_QUEUE_NAME 的消息!")
        logging.debug("消息类型：" + str(type(body_str)))
        logging.debug("消息内容：" + body_str)
        # 将body_str转换为ResumeAnalysisDTO对象
        resume_delete_request = ResumeAnalysisDTO.model_validate_json(body_str)
        # 获取要删除的简历ID
        resume_id = resume_delete_request.resumeId
        logging.info(f"Deleting resume with ID: {resume_id} from vector database.")
        # 将ID对应的简历从向量数据库中删除
        resume_vectordb.delete([str(resume_id)])
        logging.info(f"Successfully deleted resume with ID: {resume_id} from vector database.")
        # 删除完毕后手动确认消息
        ch.basic_ack(delivery_tag=delivery_tag, multiple=False)
    except Exception as e:
        logging.error(f"Error deleting resume with ID: {resume_id} from vector database: {e}")
        # 如果处理失败，拒绝消息并且不再重新入队（已经配置了死信交换机，消费失败的消息会转发到相应的死信队列）
        ch.basic_nack(delivery_tag=delivery_tag, multiple=False, requeue=False)
        return


def jd_delete_callback(ch: Channel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
    """
    Callback function to handle JD delete requests from RabbitMQ.
    :param ch: Channel
    :param method: Method
    :param properties: Properties
    :param body: Message body
    """
    jd_id = None
    delivery_tag = method.delivery_tag
    try:
        print(" [x] Received JD delete request:", body)
        # 在这里添加处理JD删除请求的逻辑
        # 例如，从数据库中删除JD记录，清理相关资源等
        print(" [x] JD delete request processed")
        # 首先将body转换为字符串
        body_str = body.decode('utf-8')
        logging.info(f"接收到来自queue: JD_DELETE_QUEUE_NAME 的消息!")
        logging.debug("消息类型：" + str(type(body_str)))
        logging.debug("消息内容：" + body_str)
        # 将body_str转换为ResumeAnalysisDTO对象
        jd_delete_request = ResumeAnalysisDTO.model_validate_json(body_str)
        # 获取要删除的JD ID
        jd_id = jd_delete_request.jdID
        logging.info(f"Deleting JD with ID: {jd_id} from vector database.")
        # 在这里添加处理JD删除请求的逻辑
        JD_vectordb.delete([str(jd_id)])
        logging.info(f"Successfully deleted JD with ID: {jd_id} from vector database.")
        # 删除完毕后手动确认消息
        ch.basic_ack(delivery_tag=delivery_tag, multiple=False)
    except Exception as e:
        logging.error(f"Error deleting JD with ID: {jd_id} from vector database: {e}")
        # 如果处理失败，拒绝消息并且不再重新入队（已经配置了死信交换机，消费失败的消息会转发到相应的死信队列）
        ch.basic_nack(delivery_tag=delivery_tag, multiple=False, requeue=False)
        return
