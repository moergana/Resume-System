import logging

from sqlalchemy import text

from ResumeAnalyse.Extractor import extract_file_to_markdown
from ResumeAnalyse.eval_workflow.vectorize import add_JDs_to_vector_db, add_resumes_to_vector_db, handle_JD_contents, handle_resumes_contents
from ResumeAnalyse.eval_workflow.summary import JD_summarize, resume_summarize
from ResumeAnalyse.constants import *
from ResumeAnalyse.eval_workflow.commons import mysql_engine


# Extractor.extract_file_to_markdown 方法支持处理的文件类型
support_file_types = [
    # PDF
    PDF_FILE_SUFFIX,
    # DOC
    DOC_FILE_SUFFIX,
    # DOCX
    DOCX_FILE_SUFFIX,
    # PPT
    PPT_FILE_SUFFIX,
    # PPTX
    PPTX_FILE_SUFFIX,
    # 图片
    *IMAGE_FILE_SUFFIX_LIST
]


def extract_and_summarize_node(state, config):
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
        if state.get("raw_resume_text", "") != "":
            logging.info("未提供简历文件路径，但已提供原始简历文本内容，对原始简历文本进行总结。")
            resume_summary = resume_summarize(state.get("raw_resume_text", ""))
            resume_summary_text = handle_resumes_contents([resume_summary])[0]
            state["resume_summary_text"] = resume_summary_text  # 将简历摘要文本保存到state中，以便后续使用
        else:
            if state.get("resume_summary_text", "") == "":
                logging.warning("未提供简历文件路径，且简历摘要内容为空。")
            else:
                resume_summary_text = state.get("resume_summary_text", "")
                logging.info("已提供简历摘要内容，跳过简历文件处理步骤。")
    else:
        # 如果提供了简历文件路径，则处理该文件
        # 判断文件是否为支持的格式
        if not resume_path.lower().endswith(tuple(support_file_types)):
            logging.error("文件格式错误：支持的文件格式为：" + ", ".join(support_file_types))
            return state
        md = extract_file_to_markdown(resume_path)
        # 记录日志
        logging.info("成功提取文件内容，生成Markdown文本。")
        state["raw_resume_text"] = md  # 将提取到的Markdown文本保存到state中，以便后续使用
        state["log_msg"].append("成功提取文件内容，生成Markdown文本。\n")
        # 使用LLM总结简历内容
        resume_summary = resume_summarize(md)
        # 将得到的Pydantic对象转换为字符串
        resume_summary_text = handle_resumes_contents([resume_summary])[0]  # 注意handle_resumes_contents返回的类型是List[str]
        state["resume_summary_text"] = resume_summary_text  # 将简历摘要文本保存到state中，以便后续使用

    # 处理JD PDF文件，提取内容并生成Markdown文本，之后用LLM总结JD内容
    JD_path = state.get("jd_path", "")
    if JD_path == "":
        # 如果不提供JD文件路径，则查看是否已经提供了JD摘要内容
        logging.info("未提供JD文件路径!")
        if state.get("raw_jd_text", "") != "":
            logging.info("未提供JD文件路径，但已提供原始JD文本内容，对原始JD文本进行总结。")
            jd_summary = JD_summarize(state.get("raw_jd_text", ""))
            jd_summary_text = handle_JD_contents([jd_summary])[0]
            state["jd_summary_text"] = jd_summary_text  # 将JD摘要文本保存到state中，以便后续使用
        else:
            if state.get("jd_summary_text", "") == "":
                logging.warning("未提供JD文件路径，且JD摘要内容为空")
            else:
                jd_summary_text = state.get("jd_summary_text", "")
                logging.info("已提供JD摘要内容，跳过JD文件处理步骤。")
    else:
        # 如果提供了JD文件路径，则处理该文件
        # 判断文件是否为支持的格式
        if not JD_path.lower().endswith(tuple(support_file_types)):
            logging.error("文件格式错误：支持的文件格式为：" + ", ".join(support_file_types))
            return state
        md = extract_file_to_markdown(JD_path)
        # 记录日志
        logging.info("成功提取JD文件内容，生成Markdown文本。")
        state["raw_jd_text"] = md  # 将提取到的Markdown文本保存到state中，以便后续使用
        state["log_msg"].append("成功提取JD文件内容，生成Markdown文本。\n")
        # 使用LLM总结JD内容
        jd_summary = JD_summarize(md)
        # 将得到的Pydantic对象转换为字符串
        jd_summary_text = handle_JD_contents([jd_summary])[0]  # 注意handle_JD_contents方法返回的类型是List[str]
        state["jd_summary_text"] = jd_summary_text  # 将JD摘要文本保存到state中，以便后续使用

    return state
    
    
def resume_vectorize_node(state, config):
    """
    LangGraph 结点
    将简历和JD内容添加到向量数据库中
    之后根据用户请求类型路由到下一个结点
    :param state:
    :param config:
    :return:
    """
    if state.get("resume_id", "") == "":
        logging.error("简历ID为空，无法将简历内容添加到向量数据库中。")
        return state
    
    # 首先调用extract_and_summarize_node结点，根据state中指定的简历和JD文件路径，处理文件
    # 提取内容并生成Markdown文本，然后用LLM总结简历和JD内容，并将结果保存回state中，以便后续使用
    extract_and_summarize_node(state, config)
    
    if state.get("raw_resume_text", "") == "" or state.get("resume_summary_text", "") == "":
        logging.error("简历内容为空，无法添加到向量数据库中。")
        return state

    # 将简历内容保存到MySQL数据库中
    logging.info(f"Saving resume and summary texts to MySQL tb_resume.")
    with mysql_engine.connect() as connection:
        result = connection.execute(
            text("""INSERT INTO tb_resume 
            (resume_id, file_path, raw_text, summary, create_time)
                VALUES (:resume_id, :file_path, :raw_text, :summary, :create_time)"""),
            {
                "resume_id": state.get("resume_id", ""),
                "file_path": state.get("resume_path", ""),
                "raw_text": state.get("raw_resume_text", ""),
                "summary": state.get("resume_summary_text", ""),
                "create_time": state.get("resume_create_time", "")
            }
        )
        # 注意：对于INSERT、UPDATE、DELETE等操作，需要手动提交事务才能实现修改
        connection.commit()
        # 检查是否插入成功
        if result.rowcount == 0:
            logging.error(f"Failed to saved summary texts to MySQL tb_resume.")
            return state
        else:
            logging.info(f"Successfully saved summary texts to MySQL tb_resume.")
            id = result.lastrowid  # 获取新插入记录的ID
            logging.info(f"New resume record ID: {id}.")
        
    # 将简历内容添加到向量数据库中
    logging.info("请求类型为：resume_upload。正在将简历内容添加到向量数据库中...")
    summary_text = state.get("resume_summary_text", "")
    resume_id = state.get("resume_id", "")
    resume_id = str(resume_id)  # 将resume_id强制转换为字符串类型
    add_resumes_to_vector_db([summary_text], [resume_id])
    logging.info("简历内容已成功添加到向量数据库中。")
    state["log_msg"].append("简历内容已成功添加到向量数据库中。\n")


def JD_vectorize_node(state, config):
    """
    LangGraph 结点
    将JD内容添加到向量数据库中
    之后根据用户请求类型路由到下一个结点
    :param state:
    :param config:
    :return:
    """
    if state.get("jd_id", "") == "":
        logging.error("JD ID为空，无法将JD内容添加到向量数据库中。")
        return state
    
    # 首先调用extract_and_summarize_node结点，根据state中指定的简历和JD文件路径，处理文件
    # 提取内容并生成Markdown文本，然后用LLM总结简历和JD内容
    extract_and_summarize_node(state, config)
    
    if state.get("raw_jd_text", "") == "" or state.get("jd_summary_text", "") == "":
        logging.error("JD内容为空，无法添加到向量数据库中。")
        return state

    # 将JD内容也保存到MySQL数据库中
    logging.info(f"Saving JD and summary texts to MySQL tb_jd.")
    with mysql_engine.connect() as connection:
        result = connection.execute(
            text("""INSERT INTO tb_jd 
            (jd_id, file_path, raw_text, summary, create_time)
                VALUES (:jd_id, :file_path, :raw_text, :summary, :create_time)"""),
            {
                "jd_id": state.get("jd_id", ""),
                "file_path": state.get("jd_path", ""),
                "raw_text": state.get("raw_jd_text", ""),
                "summary": state.get("jd_summary_text", ""),
                "create_time": state.get("jd_create_time", "")
            }
        )
        # 注意：对于INSERT、UPDATE、DELETE等操作，需要手动提交事务才能实现修改
        connection.commit()
        # 检查是否插入成功
        if result.rowcount == 0:
            logging.error(f"Failed to saved summary texts to MySQL tb_jd.")
            return state
        else:
            logging.info(f"Successfully saved summary texts to MySQL tb_jd.")
            id = result.lastrowid  # 获取新插入记录的ID
            logging.info(f"New JD record ID: {id}.")

    # 将JD内容添加到向量数据库中
    logging.info("请求类型为：jd_upload。正在将JD内容添加到向量数据库中...")
    jd_summary_text = state.get("jd_summary_text", "")
    jd_id = state.get("jd_id", "")
    jd_id = str(jd_id)  # 将jd_id强制转换为字符串类型
    add_JDs_to_vector_db([jd_summary_text], [jd_id])
    logging.info("JD内容已成功添加到向量数据库中。")
    state["log_msg"].append("JD内容已成功添加到向量数据库中。\n")