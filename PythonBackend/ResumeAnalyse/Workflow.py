import logging
import os
import uuid

from httpx import request
from langchain_core.runnables import RunnableConfig
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.types import Command, Send

from ResumeAnalyse.Analyser import generate_advice, generate_difference
from ResumeAnalyse.Extractor import extract_file_to_markdown
from ResumeAnalyse.Summarizer import resume_summarize, JD_summarize
from ResumeAnalyse.Vectorizer import add_JDs_to_vector_db, handle_resumes_contents, add_resumes_to_vector_db, \
    handle_JD_contents, \
    retrieve_resumes, retrieve_JDs
from ResumeAnalyse.constants import *
from ResumeAnalyse.entity.state import GraphState
from ResumeAnalyse.utils import support_file_types


def extract_and_summarize_node(state: GraphState, config: RunnableConfig):
    """
    LangGraph 结点
    从state中尝试获取resume和jd，然后处理文件，提取内容并生成Markdown文本，之后用LLM总结简历和JD内容
    文件的格式必须为以下种类之一：PDF、DOCX、PPTX、图片（包括PNG、JPEG、TIFF、BMP、WEBP），结点运行时要对文件格式进行确认
    :param state: GraphState
    :param config: RunnableConfig
    :return: Command
    """
    # 处理简历PDF文件，提取内容并生成Markdown文本，之后用LLM总结简历内容
    resume_path = state.get("resume_path", "")
    request_type = state.get("request_type", "")

    if resume_path == "":
        # 如果不提供简历文件路径，则查看是否已经提供了简历摘要内容
        logging.info("未提供简历文件路径!")
        if state.get("resume_summary_text", "") == "":
            logging.info("未提供简历文件路径，且简历摘要内容为空。")
            # 如果请求类型是：JD上传、为JD匹配简历
            # 则不需要简历的内容，即使简历内容为空也可以继续运行
            if request_type != REQUEST_JD_UPLOAD and request_type != REQUEST_RESUME_MATCH:
                logging.error(f"当前请求类型为 {request_type} ，但获取不到简历内容，无法继续执行Graph。")
                state["log_msg"].append("未提供简历文件路径，且简历摘要内容为空，无法继续执行Graph。\n")
                return Command(goto=END)
            else:
                logging.info(f"继续执行Graph，当前请求类型 {request_type} 不需要简历内容。")
                resume_summary_text = ""
        else:
            resume_summary_text = state.get("resume_summary_text", "")
            logging.info("已提供简历摘要内容，跳过简历文件处理步骤。")
    else:
        # 如果提供了简历文件路径，则处理该文件
        # 判断文件是否为支持的格式
        if not resume_path.lower().endswith(tuple(support_file_types)):
            logging.error("文件格式错误：支持的文件格式为：" + ", ".join(support_file_types))
            return Command(goto=END,
                           update={"log_msg": ["简历文件格式错误：支持的文件格式为：" + ", ".join(support_file_types) + "\n"]}
                        )
        md = extract_file_to_markdown(resume_path)
        # 记录日志
        logging.info("成功提取文件内容，生成Markdown文本。")
        state["log_msg"].append("成功提取文件内容，生成Markdown文本。\n")
        # 使用LLM总结简历内容
        resume_summary = resume_summarize(md)
        # 将得到的Pydantic对象转换为字符串
        resume_summary_text = handle_resumes_contents([resume_summary])[0]  # 注意handle_resumes_contents返回的类型是List[str]

    # 处理JD PDF文件，提取内容并生成Markdown文本，之后用LLM总结JD内容
    JD_path = state.get("jd_path", "")
    if JD_path == "":
        # 如果不提供JD文件路径，则查看是否已经提供了JD摘要内容
        logging.info("未提供JD文件路径!")
        if state.get("jd_summary_text", "") == "":
            logging.info("未提供JD文件路径，且JD摘要内容为空")
            # 如果请求类型是：简历上传、为简历匹配JD
            # 则不需要简历的内容，即使简历内容为空也可以继续运行
            if request_type != REQUEST_RESUME_UPLOAD and request_type != REQUEST_JD_MATCH:
                logging.error(f"当前请求类型为{request_type}，但获取不到JD内容，无法继续执行Graph。")
                state["log_msg"].append("请求类型为{request_type}，未提供JD文件路径，且JD摘要内容为空，无法继续执行Graph。\n")
                return Command(goto=END)
            else:
                logging.info(f"继续执行Graph，当前请求类型 {request_type} 不需要JD内容。")
                jd_summary_text = ""
        else:
            jd_summary_text = state.get("jd_summary_text", "")
            logging.info("已提供JD摘要内容，跳过JD文件处理步骤。")
    else:
        # 如果提供了JD文件路径，则处理该文件
        # 判断文件是否为支持的格式
        if not JD_path.lower().endswith(tuple(support_file_types)):
            logging.error("文件格式错误：支持的文件格式为：" + ", ".join(support_file_types))
            return Command(goto=END,
                           update={"log_msg": ["JD文件格式错误：支持的文件格式为：" + ", ".join(support_file_types) + "\n"]}
                        )
        md = extract_file_to_markdown(JD_path)
        # 记录日志
        logging.info("成功提取JD文件内容，生成Markdown文本。")
        state["log_msg"].append("成功提取JD文件内容，生成Markdown文本。\n")
        # 使用LLM总结JD内容
        jd_summary = JD_summarize(md)
        # 将得到的Pydantic对象转换为字符串
        jd_summary_text = handle_JD_contents([jd_summary])[0]  # 注意handle_JD_contents方法返回的类型是List[str]

    # goto: vectorize_node
    return Command(
        goto="vectorize_node",
        update={
            "resume_summary_text": resume_summary_text,
            "jd_summary_text": jd_summary_text
        }
    )


def vectorize_node(state: GraphState, config: RunnableConfig):
    """
    LangGraph 结点
    将简历和JD内容添加到向量数据库中
    之后根据用户请求类型路由到下一个结点
    :param state:
    :param config:
    :return:
    """
    # 获取用户的请求类型
    request_type = state.get("request_type", "")

    # 将简历内容添加到向量数据库中
    if request_type == REQUEST_RESUME_UPLOAD:
        # 如果请求类型为上传简历，则将简历的概述和ID写入向量数据库
        logging.info("请求类型为：resume_upload。正在将简历内容添加到向量数据库中...")
        summary_text = state.get("resume_summary_text", "")
        resume_id = state.get("resume_id", "")
        resume_id = str(resume_id)  # 将resume_id强制转换为字符串类型
        add_resumes_to_vector_db([summary_text], [resume_id])
        logging.info("简历内容已成功添加到向量数据库中。")
        state["log_msg"].append("简历内容已成功添加到向量数据库中。\n")

    # 将JD内容添加到向量数据库中
    if request_type == REQUEST_JD_UPLOAD:
        logging.info("请求类型为：jd_upload。正在将JD内容添加到向量数据库中...")
        jd_summary_text = state.get("jd_summary_text", "")
        jd_id = state.get("jd_id", "")
        jd_id = str(jd_id)  # 将resume_id强制转换为字符串类型
        add_JDs_to_vector_db([jd_summary_text], [jd_id])
        logging.info("JD内容已成功添加到向量数据库中。")
        state["log_msg"].append("JD内容已成功添加到向量数据库中。\n")

    """根据用户请求类型路由到下一个结点"""
    # 如果是resume_upload请求，将简历保存到向量数据库之后就结束了
    if request_type == REQUEST_RESUME_UPLOAD:
        logging.info("简历上传请求处理完成，结束Graph执行。")
        state["log_msg"].append("简历上传请求处理完成，结束Graph执行。\n")
        return Command(goto=END)

    # 如果是jd_upload请求，将JD保存到向量数据库之后就结束了
    if request_type == REQUEST_JD_UPLOAD:
        logging.info("JD上传请求处理完成，结束Graph执行。")
        state["log_msg"].append("JD上传请求处理完成，结束Graph执行。\n")
        return Command(goto=END)

    # 如果是resume_jd_differ请求，路由到简历与JD差异分析结点
    if request_type == REQUEST_RESUME_JD_DIFFER:
        logging.info("路由到简历与JD差异分析结点。")
        state["log_msg"].append("路由到简历与JD差异分析结点。\n")
        return Command(goto="difference_node")

    # 如果是resume_advise请求，路由到简历建议结点
    if request_type == REQUEST_RESUME_ADVISE:
        logging.info("路由到简历建议结点。")
        state["log_msg"].append("路由到简历建议结点。\n")
        return Command(goto="resume_advise_node")

    # 如果是jd_match请求，路由到JD匹配搜索结点
    if request_type == REQUEST_JD_MATCH:
        logging.info("路由到JD匹配搜索结点。")
        state["log_msg"].append("路由到JD匹配搜索结点。\n")
        return Command(goto="jd_match_node")

    # 如果是resume_match请求，路由到简历匹配搜索结点
    if request_type == REQUEST_RESUME_MATCH:
        logging.info("路由到简历匹配搜索结点。")
        state["log_msg"].append("路由到简历匹配搜索结点。\n")
        return Command(goto="resume_match_node")

    # 其他请求类型，结束Graph执行
    logging.error("未知的请求类型，结束Graph执行。")
    state["log_msg"].append("未知的请求类型，结束Graph执行。\n")
    return Command(goto=END)


def difference_node(state: GraphState, config: RunnableConfig):
    """
    LangGraph 结点
    根据state中的resume_summary 和 jd_summary，分析简历摘要和JD摘要的相似度分数和差异点
    :param state:
    :param config:
    :return:
    """
    resume_summary_text = state.get("resume_summary_text", "")
    jd_summary_text = state.get("jd_summary_text", "")

    logging.info("正在分析简历摘要和JD摘要的相似度分数和差异点。")

    difference = generate_difference(
        resume_content=resume_summary_text,
        jd_content=jd_summary_text
    )

    logging.info("简历摘要和JD摘要的相似度分析完成。")
    state["log_msg"].append("简历摘要和JD摘要的相似度分析完成。\n")
    logging.debug(f"Match Score: {difference.match_score}")
    logging.debug(f"Difference Points: {difference.differences}")

    # goto: END
    return Command(
        update={
            "match_score": difference.match_score,
            "differences": difference.differences
        }
    )


def resume_advise_node(state: GraphState, config: RunnableConfig):
    """
    LangGraph 结点
    根据state中的resume_summary 和 jd_summary，为简历和求职提供改进建议
    :param state:
    :param config:
    :return:
    """
    resume_summary_text = state.get("resume_summary_text", "")
    jd_summary_text = state.get("jd_summary_text", "")

    logging.info("正在生成简历改进建议和求职建议。")

    advice = generate_advice(
        resume_content=resume_summary_text,
        jd_content=jd_summary_text
    )

    logging.info("简历改进建议和求职建议生成完成。")
    state["log_msg"].append("简历改进建议和求职建议生成完成。\n")
    logging.debug(f"Match Score: {advice.match_score}")
    logging.debug(f"Improvement Suggestions: {advice.improvement_suggestions}")
    logging.debug(f"Job Hunting Tips: {advice.job_hunting_tips}")

    # goto: END
    return Command(
        update={
            "match_score": advice.match_score,
            "improvement_suggestions": advice.improvement_suggestions,
            "job_hunting_tips": advice.job_hunting_tips
        }
    )


def jd_match_node(state: GraphState, config: RunnableConfig):
    """
    LangGraph 结点
    根据state中的resume_summary，为用户推荐匹配的JD列表
    :param state:
    :param config:
    :return:
    """
    logging.info("正在根据简历摘要检索匹配的JD列表。")
    matched_jds = retrieve_JDs(
        resume=state.get("resume_summary_text", ""),
        search_type="similarity",
        k=4,
        fetch_k=4 * 5,
        lambda_mult=0.5
    )
    logging.info("JD列表检索完成。")

    # goto: END
    return Command(
        update={
            "retrieved_jds": matched_jds
        }
    )


def resume_match_node(state: GraphState, config: RunnableConfig):
    """
    LangGraph 结点
    根据state中的jd_summary，为用户推荐匹配的简历列表
    :param state:
    :param config:
    :return:
    """
    logging.info("正在根据JD摘要检索匹配的简历列表。")
    matched_resumes = retrieve_resumes(
        JD=state.get("jd_summary_text", ""),
        search_type="similarity",
        k=4,
        fetch_k=4 * 5,
        lambda_mult=0.5
    )
    logging.info("简历列表检索完成。")

    # goto: END
    return Command(
        update={
            "retrieved_resumes": matched_resumes
        }
    )


"""
定义StateGraph
"""
# StateGraph的state_schema指定了Graph的全局状态类型，该状态可以随着Graph的执行变化和修改内容，
# 且会被记录到checkpointer中（如果graph.compile参数内传递了checkpointer）。必须要指定。
# context_schema用于设置Graph的配置信息，保存的是全程共享、但不随节点修改的上下文。不会被写入checkpointer。默认为None。
# input_schema指定了用户在调用Graph时，必须提供的数据结构。默认与state_schema相同。
# output_schema指定了Graph执行完成后，对外返回的数据结构。默认与state_schema相同。
graph = StateGraph(
    state_schema=GraphState
)
"""
定义Graph中的结点
"""
graph.add_node("pdf_extract_and_summarize_node", extract_and_summarize_node)
graph.add_node("vectorize_node", vectorize_node)
graph.add_node("difference_node", difference_node)
graph.add_node("resume_advise_node", resume_advise_node)
graph.add_node("jd_match_node", jd_match_node)
graph.add_node("resume_match_node", resume_match_node)

"""
定义Graph中的静态边
需要注意：动态路由的边不需要在这里定义，而是在结点函数中通过Command的goto参数指定
这里定义的edge是Graph的静态执行流程，无论动态路由Command是否被执行，静态路由edge都一定会被执行
"""
graph.add_edge(START, "pdf_extract_and_summarize_node")
graph.add_edge("difference_node", END)
graph.add_edge("resume_advise_node", END)
graph.add_edge("jd_match_node", END)
graph.add_edge("resume_match_node", END)

# 编译Graph，生成可执行的GraphExecutor
graph_executor = graph.compile()


def execute_graph(initial_state: GraphState) -> dict:
    """
    同步执行Graph，返回最终状态
    如果请求类型为resume_advise，那么Graph执行过程中就会生成简历分析的相关结果，这些结果会被保存到final_state中。
    同时还需要生成一个唯一的resume_analysis_id，标识此次分析结果，以供后续查询使用
    :param initial_state:
    :return:
    """
    final_state = graph_executor.invoke(initial_state)
    # if initial_state.get("request_type", "") == "resume_advise":
    #     resume_analysis_id = initial_state.get("user_id", "") + "-" + uuid.uuid4().hex
    #     final_state["resume_analysis_id"] = resume_analysis_id
    return final_state


if __name__ == "__main__":
    # 测试代码
    initial_state: GraphState = {
        "messages": [],

        "user_id": "user_123",
        "request_type": "resume_advise",

        "resume_path": "sample_data/sample_resume.pdf",
        "jd_path": "sample_data/sample_jd.pdf",
        "resume_id": "resume_123",
        "jd_id": "jd_123",
        "resume_summary_text": "",
        "jd_summary_text": "",

        "match_score": -1,
        "differences": "",
        "improvement_suggestions": "",
        "job_hunting_tips": "",

        "retrieved_resumes": [],
        "retrieved_jds": [],

        "status": "",
        "log_msg": [],
    }
    final_state = graph_executor.invoke(initial_state)
    print("Final State:", final_state)
