import logging

from ResumeAnalyse.Workflow import execute_graph
from ResumeAnalyse.constants import RESUME_ANALYSIS_FINISHED_STATUS, RESUME_ANALYSIS_FAILED_STATUS
from ResumeAnalyse.entity.resume_analysis_dto import ResumeAnalysisDTO
from ResumeAnalyse.rabbitmq.constants import *
from ResumeAnalyse.rabbitmq.utils import generate_jd_summary_text


def resume_upload_callback(ch, method, properties, body):
    """
    Callback function to handle resume upload messages from RabbitMQ.
    负责处理请求类型：REQUEST_RESUME_UPLOAD
    :param ch: Channel
    :param method: Method
    :param properties: Properties
    :param body: Message body
    """
    delivery_tag = method.delivery_tag
    initial_state = {}
    try:
        # 首先将body转换为字符串
        body_str = body.decode('utf-8')
        logging.info(f"接收到来自queue: {RESUME_UPLOAD_QUEUE_NAME} 的消息!")
        logging.debug("消息类型：" + str(type(body_str)))
        logging.debug("消息内容：" + body_str)
        # 将body_str转换为ResumeAnalysisDTO对象
        resume_upload_request = ResumeAnalysisDTO.model_validate_json(body_str)

        # 构造initial_state
        initial_state = {
            "messages": [],

            "user_id": str(resume_upload_request.userId),
            "request_type": resume_upload_request.requestType,

            "resume_id": str(resume_upload_request.resumeId),
            "resume_path": resume_upload_request.resumeFilePath,
            "resume_summary_text": "",

            "jd_id": -1,
            "jd_path": "",
            "jd_summary_text": "",

            "match_score": -1,
            "differences": "",
            "improvement_suggestions": "",
            "job_hunting_tips": "",

            "retrieved_resumes": [],
            "retrieved_jds": [],

            "status": resume_upload_request.status,
            "log_msg": [],
        }

        # 开始执行工作流
        final_state = execute_graph(initial_state)
        logging.info(f"Resume upload successfully! resume ID: {resume_upload_request.resumeId}")
        final_state["status"] = RESUME_ANALYSIS_FINISHED_STATUS

        # 处理完毕，手动确认消息
        ch.basic_ack(delivery_tag=delivery_tag, multiple=False)

    except Exception as e:
        logging.error(f"Error during resume upload execution: {e}")
        final_state = initial_state
        final_state["status"] = RESUME_ANALYSIS_FAILED_STATUS
        final_state["log_msg"].append(f"Error: {str(e)}")
        # 如果处理失败，拒绝消息并且不再重新入队（已经配置了死信交换机，消费失败的消息会转发到相应的死信队列）
        ch.basic_nack(delivery_tag=delivery_tag, multiple=False, requeue=False)
        return


def jd_upload_callback(ch, method, properties, body):
    """
    Callback function to handle JD upload messages from RabbitMQ.
    负责处理请求类型：REQUEST_JD_UPLOAD
    :param ch: Channel
    :param method: Method
    :param properties: Properties
    :param body: Message body
    """
    delivery_tag = method.delivery_tag
    initial_state = {}
    try:
        # 首先将body转换为字符串
        body_str = body.decode('utf-8')
        logging.info(f"接收到来自queue: {JD_UPLOAD_QUEUE_NAME} 的消息!")
        logging.debug("消息类型：" + str(type(body_str)))
        logging.debug("消息内容：" + body_str)
        # 将body_str转换为ResumeAnalysisDTO对象
        jd_upload_request = ResumeAnalysisDTO.model_validate_json(body_str)

        # 构造initial_state
        initial_state = {
            "messages": [],

            "user_id": str(jd_upload_request.userId),
            "request_type": jd_upload_request.requestType,

            "resume_id": -1,
            "resume_path": "",
            "resume_summary_text": "",

            "jd_id": str(jd_upload_request.jdID),
            "jd_path": jd_upload_request.jdFilePath,
            "jd_summary_text": "",

            "match_score": -1,
            "differences": "",
            "improvement_suggestions": "",
            "job_hunting_tips": "",

            "retrieved_resumes": [],
            "retrieved_jds": [],

            "status": jd_upload_request.status,
            "log_msg": [],
        }

        if (jd_upload_request.jdFilePath is None) or (jd_upload_request.jdFilePath == ""):
            initial_state["jd_summary_text"] = generate_jd_summary_text(jd_upload_request)

        # 开始执行工作流
        final_state = execute_graph(initial_state)
        logging.info(f"JD upload successfully! JD ID: {jd_upload_request.jdID}")
        final_state["status"] = RESUME_ANALYSIS_FINISHED_STATUS

        # 处理完毕，手动确认消息
        ch.basic_ack(delivery_tag=delivery_tag, multiple=False)

    except Exception as e:
        logging.error(f"Error during JD upload execution: {e}")
        final_state = initial_state
        final_state["status"] = RESUME_ANALYSIS_FAILED_STATUS
        final_state["log_msg"].append(f"Error: {str(e)}")
        # 如果处理失败，拒绝消息并且不再重新入队（已经配置了死信交换机，消费失败的消息会转发到相应的死信队列）
        ch.basic_nack(delivery_tag=delivery_tag, multiple=False, requeue=False)
        return
