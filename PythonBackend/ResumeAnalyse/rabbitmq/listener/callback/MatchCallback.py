import logging
import ResumeAnalyse.rabbitmq.utils

from ResumeAnalyse.Workflow import execute_graph
import json

from ResumeAnalyse.constants import *
from ResumeAnalyse.rabbitmq.constants import *
from ResumeAnalyse.entity.resume_analysis_dto import ResumeAnalysisDTO
from ResumeAnalyse.rabbitmq.utils import generate_jd_summary_text


def jd_match_callback(ch, method, properties, body):
    """
    为上传的简历做JD匹配的回调函数。
    负责处理请求类型：REQUEST_JD_MATCH
    :param ch: 创建consumer的channel。
    :param method: 投递方法信息。
    :param properties: 消息属性。
    :param body: 消息体。
    :return: None
    """
    delivery_tag = method.delivery_tag
    initial_state = {}
    jd_match_request = ResumeAnalysisDTO()
    try:
        print(" [x] Received %r" % body)
        # 首先将body转换为字符串
        body_str = body.decode('utf-8')
        logging.info(f"接收到来自queue: {JD_MATCH_REQUEST_QUEUE_NAME} 的消息!")
        logging.debug("消息类型：" + str(type(body_str)))
        logging.debug("消息内容：" + body_str)
        # 将body_str转换为ResumeAnalysisDTO对象
        jd_match_request = ResumeAnalysisDTO.model_validate_json(body_str)

        # 构造initial_state
        initial_state = {
            "messages": [],

            "user_id": str(jd_match_request.userId),
            "request_type": jd_match_request.requestType,

            "resume_id": str(jd_match_request.resumeId),
            "resume_path": jd_match_request.resumeFilePath,
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

            "status": jd_match_request.status,
            "log_msg": [],
        }

        # 开始执行工作流
        final_state = execute_graph(initial_state)
        logging.info(f"JD match executed successfully for resume ID: {jd_match_request.resumeId}")
        final_state["status"] = RESUME_ANALYSIS_FINISHED_STATUS
        jd_match_result = jd_match_request
        jd_match_result.status = RESUME_ANALYSIS_FINISHED_STATUS
        jd_match_result.analysisResult = json.dumps({
            "match_score": final_state.get("match_score", -1),
            "differences": final_state.get("differences", ""),
            "improvement_suggestions": final_state.get("improvement_suggestions", ""),
            "job_hunting_tips": final_state.get("job_hunting_tips", "")
        }, ensure_ascii=False)
        jd_match_result.retrievedResumes = final_state.get("retrieved_resumes", [])
        jd_match_result.retrievedJds = final_state.get("retrieved_jds", [])
    except Exception as e:
        logging.error(f"Error during JD match execution: {e}")
        final_state = initial_state
        final_state["status"] = RESUME_ANALYSIS_FAILED_STATUS
        final_state["log_msg"].append(f"Error: {str(e)}")
        jd_match_result = jd_match_request
        jd_match_result.status = RESUME_ANALYSIS_FAILED_STATUS
        jd_match_result.analysisResult = json.dumps({
            "error": str(e)
        }, ensure_ascii=False)

    try:
        # 将final_state转为JSON字符串，并发送到结果队列
        # 不使用 model_dump_json()，而是先转字典，再用 json.dumps 配合 ensure_ascii=False
        result_dict = jd_match_result.model_dump()
        result_body_str = json.dumps(result_dict, ensure_ascii=False)
        logging.info(f"JD match workflow处理完成，准备发送结果到queue: {JD_MATCH_RESULT_QUEUE_NAME}。")
        logging.debug("消息类型：" + str(type(result_body_str)))
        logging.debug("消息内容：" + result_body_str)
        ch.basic_publish(
            exchange=MATCH_EXCHANGE_NAME,
            routing_key=JD_MATCH_RESULT_ROUTING_KEY,
            body=result_body_str
        )
        logging.info(f"Successfully processed and sent result message to queue: {JD_MATCH_RESULT_QUEUE_NAME}.")
        # 处理完毕，手动确认消息
        ch.basic_ack(delivery_tag=delivery_tag, multiple=False)

    except Exception as e:
        logging.error(f"Error sending JD match result message to queue: {e}")
        # 如果处理失败，拒绝消息并且不再重新入队（已经配置了死信交换机，消费失败的消息会转发到相应的死信队列）
        ch.basic_nack(delivery_tag=delivery_tag, multiple=False, requeue=False)
        return


def resume_match_callback(ch, method, properties, body):
    """
    为上传的JD做简历匹配的回调函数。
    负责处理请求类型：REQUEST_RESUME_MATCH
    :param ch: 创建consumer的channel。
    :param method: 投递方法信息。
    :param properties: 消息属性。
    :param body: 消息体。
    :return: None
    """
    delivery_tag = method.delivery_tag
    initial_state = {}
    resume_match_request = ResumeAnalysisDTO()
    try:
        print(" [x] Received %r" % body)
        # 首先将body转换为字符串
        body_str = body.decode('utf-8')
        logging.info(f"接收到来自queue: {RESUME_MATCH_REQUEST_QUEUE_NAME} 的消息!")
        logging.debug("消息类型：" + str(type(body_str)))
        logging.debug("消息内容：" + body_str)
        # 将body_str转换为ResumeAnalysisDTO对象
        resume_match_request = ResumeAnalysisDTO.model_validate_json(body_str)
        print(resume_match_request)

        # 构造initial_state
        initial_state = {
            "messages": [],

            "user_id": str(resume_match_request.userId),
            "request_type": resume_match_request.requestType,

            "resume_id": -1,
            "resume_path": "",
            "resume_summary_text": "",

            "jd_id": str(resume_match_request.jdID),
            "jd_path": resume_match_request.jdFilePath,
            "jd_summary_text": "",

            "match_score": -1,
            "differences": "",
            "improvement_suggestions": "",
            "job_hunting_tips": "",

            "retrieved_resumes": [],
            "retrieved_jds": [],

            "status": resume_match_request.status,
            "log_msg": [],
        }

        if (resume_match_request.jdFilePath is None) or (resume_match_request.jdFilePath == ""):
            initial_state["jd_summary_text"] = generate_jd_summary_text(resume_match_request)

        # 开始执行工作流
        final_state = execute_graph(initial_state)
        logging.info(f"Resume match executed successfully for JD ID: {resume_match_request.jdID}")
        final_state["status"] = RESUME_ANALYSIS_FINISHED_STATUS
        resume_match_result = resume_match_request
        resume_match_result.status = RESUME_ANALYSIS_FINISHED_STATUS
        resume_match_result.analysisResult = json.dumps({
            "match_score": final_state.get("match_score", -1),
            "differences": final_state.get("differences", ""),
            "improvement_suggestions": final_state.get("improvement_suggestions", ""),
            "job_hunting_tips": final_state.get("job_hunting_tips", "")
        }, ensure_ascii=False)
        resume_match_result.retrievedResumes = final_state.get("retrieved_resumes", [])
        resume_match_result.retrievedJds = final_state.get("retrieved_jds", [])
    except Exception as e:
        logging.error(f"Error during resume match execution: {e}")
        final_state = initial_state
        final_state["status"] = RESUME_ANALYSIS_FAILED_STATUS
        final_state["log_msg"].append(f"Error: {str(e)}")
        resume_match_result = resume_match_request
        resume_match_result.status = RESUME_ANALYSIS_FAILED_STATUS
        resume_match_result.analysisResult = json.dumps({
            "error": str(e)
        }, ensure_ascii=False)

    try:
        # 将final_state转为JSON字符串，并发送到结果队列
        # 不使用 model_dump_json()，而是先转字典，再用 json.dumps 配合 ensure_ascii=False
        result_dict = resume_match_result.model_dump()
        result_body_str = json.dumps(result_dict, ensure_ascii=False)
        logging.info(f"Resume match workflow处理完成，准备发送结果到queue: {RESUME_MATCH_RESULT_QUEUE_NAME}。")
        logging.debug("消息类型：" + str(type(result_body_str)))
        logging.debug("消息内容：" + result_body_str)
        ch.basic_publish(
            exchange=MATCH_EXCHANGE_NAME,
            routing_key=RESUME_MATCH_RESULT_ROUTING_KEY,
            body=result_body_str
        )
        logging.info(f"Successfully processed and sent result message to queue: {RESUME_MATCH_RESULT_QUEUE_NAME}.")

        # 处理完毕，手动确认消息
        ch.basic_ack(delivery_tag=delivery_tag, multiple=False)

    except Exception as e:
        logging.error(f"Error sending resume match result message to queue: {e}")
        # 如果处理失败，拒绝消息并且不再重新入队（已经配置了死信交换机，消费失败的消息会转发到相应的死信队列）
        ch.basic_nack(delivery_tag=delivery_tag, multiple=False, requeue=False)
        return
