import json
import logging

from ResumeAnalyse.Workflow import execute_graph
from ResumeAnalyse.constants import RESUME_ANALYSIS_FINISHED_STATUS, RESUME_ANALYSIS_FAILED_STATUS, \
    get_resume_analysis_redis_key, RESUME_ANALYSIS_REDIS_TTL
from ResumeAnalyse.entity.resume_analysis_dto import ResumeAnalysisDTO
from ResumeAnalyse.rabbitmq.constants import *
from ResumeAnalyse.rabbitmq.utils import generate_jd_summary_text
from ResumeAnalyse.utils import redis_client


def resume_analyse_callback(ch, method, properties, body):
    """
    简历分析和建议的回调函数。
    负责处理请求类型：REQUEST_RESUME_JD_DIFFER、REQUEST_RESUME_ADVISE
    :param ch: 创建consumer的channel。
    :param method: 投递方法信息，包含有关投递的元数据。
    比如交换机exchange、路由键routing_key、投递标签delivery_tag（消息在该 channel 内的唯一 ID）、是否是重投递redelivered等。
    :param properties: 消息属性，包含消息的元数据。 比如内容类型content_type、消息头headers、消息IDmessage_id、时间戳timestamp等。
    这些属性可以用来传递消息的附加信息，或者用于消息的路由和处理。
    :param body: 消息体，需要通过decode方法（参数指定解码方式）转换为字符串。
    :return: None
    """
    delivery_tag = method.delivery_tag
    initial_state = {}
    resume_analysis_request = ResumeAnalysisDTO()
    try:
        print(" [x] Received %r" % body)
        # 首先将body转换为字符串
        body_str = body.decode('utf-8')
        logging.info(f"接收到来自queue: {ANALYSE_REQUEST_QUEUE_NAME} 的消息!")
        logging.debug("消息类型：" + str(type(body_str)))
        logging.debug("消息内容：" + body_str)
        # 将body_str转换为ResumeAnalysisDTO对象
        resume_analysis_request = ResumeAnalysisDTO.model_validate_json(body_str)

        # 构造initial_state
        initial_state = {
            "messages": [],

            "user_id": str(resume_analysis_request.userId),
            "request_type": resume_analysis_request.requestType,

            "resume_id": str(resume_analysis_request.resumeId),
            "resume_path": resume_analysis_request.resumeFilePath,
            "resume_summary_text": "",

            "jd_id": str(resume_analysis_request.jdID),
            "jd_path": resume_analysis_request.jdFilePath,
            "jd_summary_text": "",

            "match_score": -1,
            "differences": "",
            "improvement_suggestions": "",
            "job_hunting_tips": "",

            "retrieved_resumes": [],
            "retrieved_jds": [],

            "status": resume_analysis_request.status,
            "log_msg": [],
        }

        if (resume_analysis_request.jdFilePath is None) or (resume_analysis_request.jdFilePath == ""):
            initial_state["jd_summary_text"] = generate_jd_summary_text(resume_analysis_request)

        # 执行工作流
        final_state = execute_graph(initial_state)
        logging.info(f"Resume Analyse executed successfully for resume ID: {resume_analysis_request.resumeId}")
        final_state["status"] = RESUME_ANALYSIS_FINISHED_STATUS
        resume_analysis_result = resume_analysis_request
        resume_analysis_result.status = RESUME_ANALYSIS_FINISHED_STATUS
        resume_analysis_result.analysisResult = json.dumps({
            "match_score": final_state.get("match_score", -1),
            "differences": final_state.get("differences", ""),
            "improvement_suggestions": final_state.get("improvement_suggestions", ""),
            "job_hunting_tips": final_state.get("job_hunting_tips", "")
        }, ensure_ascii=False)
        resume_analysis_result.retrievedResumes = final_state.get("retrieved_resumes", [])
        resume_analysis_result.retrievedJds = final_state.get("retrieved_jds", [])
    except Exception as e:
        logging.error(f"Error during workflow execution: {e}")
        final_state = initial_state
        final_state["status"] = RESUME_ANALYSIS_FAILED_STATUS
        final_state["log_msg"].append(f"Error: {str(e)}")
        resume_analysis_result = resume_analysis_request
        resume_analysis_result.status = RESUME_ANALYSIS_FAILED_STATUS
        resume_analysis_result.analysisResult = json.dumps({
            "error": str(e)
        }, ensure_ascii=False)

    try:
        # 将final_state转为JSON字符串，并发送到结果队列
        # 不使用 model_dump_json()，而是先转字典，再用 json.dumps 配合 ensure_ascii=False
        result_dict = resume_analysis_result.model_dump()
        result_body_str = json.dumps(result_dict, ensure_ascii=False)
        logging.info(f"Resume analyse workflow处理完成，准备发送结果到queue: {ANALYSE_RESULT_QUEUE_NAME}。")
        logging.debug("消息类型：" + str(type(result_body_str)))
        logging.debug("消息内容：" + result_body_str)
        ch.basic_publish(
            exchange=ANALYSE_EXCHANGE_NAME,
            routing_key=ANALYSE_RESULT_ROUTING_KEY,
            body=result_body_str
        )
        logging.info(f"Successfully processed and sent result message to queue: {ANALYSE_RESULT_QUEUE_NAME}.")

        # 将分析的结果保存到Redis中，以备聊天bot查询使用
        # 该结果在Redis中并不永久保存，而是设置了TTL过期时间
        logging.info(f"Saving resume analysis result to Redis for ID: {resume_analysis_result.id}.")
        redis_key = get_resume_analysis_redis_key(resume_analysis_result.id)
        redis_value = {
            "resume_summary_text": final_state.get("resume_summary_text", ""),
            "jd_summary_text": final_state.get("jd_summary_text", ""),
            "match_score": final_state.get("match_score", -1),
            "differences": final_state.get("differences", ""),
            "improvement_suggestions": final_state.get("improvement_suggestions", ""),
            "job_hunting_tips": final_state.get("job_hunting_tips", "")
        }
        redis_client.hset(redis_key, mapping=redis_value)
        redis_client.expire(redis_key, RESUME_ANALYSIS_REDIS_TTL)
        logging.info(f"Successfully saved resume analysis result to Redis with key: {redis_key}.")

        # 处理完毕后手动确认消息
        ch.basic_ack(delivery_tag=delivery_tag, multiple=False)

    except Exception as e:
        logging.error(f"Error sending result message to queue or saving to Redis: {e}")
        # 如果处理失败，拒绝消息并且不再重新入队（已经配置了死信交换机，消费失败的消息会转发到相应的死信队列）
        ch.basic_nack(delivery_tag=delivery_tag, multiple=False, requeue=False)
        return
