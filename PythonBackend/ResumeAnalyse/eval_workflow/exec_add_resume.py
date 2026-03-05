# 构造initial_state
from datetime import datetime
import logging
import os
from time import sleep
from unittest import result

from sqlalchemy import text

from ResumeAnalyse.eval_workflow.save_file import resume_vectorize_node, JD_vectorize_node
from ResumeAnalyse.eval_workflow.commons import mysql_engine
from ResumeAnalyse.eval_workflow.vectorize import resume_vectordb
from ResumeAnalyse.eval_workflow.save_file import support_file_types


state = {
    "resume_id": "",  # 新增resume_id字段，用于保存简历记录的ID
    "resume_path": "",  # 简历文件路径
    "raw_resume_text": "",  # 原始简历文本内容
    "resume_summary_text": "",  # LLM总结的简历文本内容
    "resume_create_time": "",  # 简历创建时间

    "jd_id": "",  # 新增jd_id字段，用于保存JD记录的ID
    "jd_path": "",  # JD文件路径
    "raw_jd_text": "",  # 原始JD文本内容
    "jd_summary_text": "",  # LLM总结的JD文本内容
    "jd_create_time": "",  # JD创建时间

    "log_msg": [],
}


def test_resume_vectorize_node():
    """
    测试resume_vectorize_node结点的功能，验证简历文件内容是否正确提取、总结，并成功添加到向量数据库中。
    请注意：在运行此测试之前，请确保已经正确配置了数据库连接，并且数据库中已经创建了相应的表结构。
    同时注意设置正确的简历文件路径，以便测试能够找到并处理该文件。
    """
    
    new_state = state.copy()  # 创建state的副本，避免修改原始state
    new_state["resume_path"] = "/root/program_projects/ResumeSystem/vacancy-resume-matching-dataset/CV_PDF/1.pdf"  # 设置简历文件路径
    new_state["resume_create_time"] = datetime.now()  # 设置创建时间为当前时间
    logging.info("Starting to process resume files.")
    updated_state = resume_vectorize_node(new_state, config={})  # 调用save_file_node函数处理文件
    logging.info("Finished processing files.")
    

def delete_resume(id: int):
    """
    根据简历ID删除数据库中对应的简历记录。
    请注意：在运行此函数之前，请确保已经正确配置了数据库连接，并且数据库中已经创建了相应的表结构。
    同时注意设置正确的简历ID，以便函数能够找到并删除对应的简历记录。
    """
    # 首先根据resume_id查询数据库，获取对应的简历记录，确认该记录存在
    # 如果记录存在，则执行DELETE操作删除该记录，并删除该id在向量数据库中对应的记录
    # 删除成功后，返回删除结果或日志信息
    with mysql_engine.connect() as connection:
        result = connection.execute(
            text("""SELECT resume_id FROM tb_resume WHERE id = :id"""),
            {
                "id": id
            }
        )
        record = result.fetchone()  # 获取查询结果
        if record is None:
            logging.error(f"No resume record found with ID: {id}. No deletion performed.")
            return
        resume_id = record.resume_id  # 获取resume_id字段的值
        logging.info(f"Found resume record with ID: {id}, resume_id: {resume_id}. Proceeding with deletion.")
        
        result = connection.execute(
            text("""DELETE FROM tb_resume WHERE id = :id"""),
            {
                "id": id
            }
        )
        connection.commit()  # 提交事务
        if result.rowcount == 0:
            logging.error(f"No resume record found with ID: {id}. No deletion performed.")
        else:
            logging.info(f"Successfully deleted resume record with ID: {id}.")
            # 删除向量数据库中对应的记录
            deleted = resume_vectordb.delete([str(resume_id)])  # 调用resume_vectordb的delete方法，根据ID删除记录
            if deleted:
                logging.info(f"Successfully deleted resume record with Resume ID: {resume_id} from vector database.")
            else:
                logging.error(f"Failed to delete resume record with Resume ID: {resume_id} from vector database.")


def vectorize_resume_dir(resume_dir: str):
    """
    批量处理简历文件夹中的所有简历文件（只处理一级目录下的文件），提取内容、总结，并添加到向量数据库中。
    请注意：在运行此函数之前，请确保已经正确配置了数据库连接，并且数据库中已经创建了相应的表结构。
    同时注意设置正确的简历文件夹路径，以便函数能够找到并处理该文件夹中的所有简历文件。
    """
    # 遍历resume_dir目录下的所有文件，调用resume_vectorize_node函数处理每个文件
    if not os.path.exists(resume_dir):
        logging.error(f"简历文件夹路径不存在: {resume_dir}")
        return
    
    try:
        for filename in os.listdir(resume_dir):
            file_path = os.path.join(resume_dir, filename)
            if os.path.isfile(file_path):  # 只处理文件，忽略子目录
                if not file_path.lower().endswith(tuple(support_file_types)):
                    logging.error(f"文件 '{file_path}' 格式错误：支持的文件格式为：" + ", ".join(support_file_types))
                    continue
                new_state = state.copy()  # 创建state的副本，避免修改原始state
                new_state["resume_id"] = filename.rsplit('.', 1)[0]  # 使用文件名（不含扩展名）作为简历ID
                new_state["resume_path"] = file_path  # 设置简历文件路径
                new_state["resume_create_time"] = datetime.now()  # 设置创建时间为当前时间
                logging.info(f"Starting to process resume file: {file_path}")
                updated_state = resume_vectorize_node(new_state, config={})  # 调用save_file_node函数处理文件
                logging.info(f"Finished processing resume file: {file_path}")
                os.remove(file_path)  # 删除处理完成的文件
                sleep(10)  # 添加适当的延迟，避免过快请求API导致限流拒绝响应
    except Exception as e:
        logging.error(f"""Error occurred while processing resume files in directory: {resume_dir}. Error details: {str(e)}
Resumes vectorization process terminated with errors.""")


if __name__ == "__main__":
    vectorize_resume_dir("/root/program_projects/ResumeSystem/vacancy-resume-matching-dataset/to_vectorize_pdf")