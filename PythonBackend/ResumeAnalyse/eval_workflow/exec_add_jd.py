# 构造initial_state
from datetime import datetime
import logging
import os
from time import sleep
from pandas import read_csv

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


def test_jd_vectorize_node():
    """
    测试resume_vectorize_node结点的功能，验证简历文件内容是否正确提取、总结，并成功添加到向量数据库中。
    请注意：在运行此测试之前，请确保已经正确配置了数据库连接，并且数据库中已经创建了相应的表结构。
    同时注意设置正确的简历文件路径，以便测试能够找到并处理该文件。
    """
    
    new_state = state.copy()  # 创建state的副本，避免修改原始state
    new_state["jd_path"] = "/root/program_projects/ResumeSystem/vacancy-resume-matching-dataset/CV_PDF/1.pdf"  # 设置JD文件路径
    new_state["jd_create_time"] = datetime.now()  # 设置创建时间为当前时间
    logging.info("Starting to process JD files.")
    updated_state = JD_vectorize_node(new_state, config={})  # 调用save_file_node函数处理文件
    logging.info("Finished processing files.")
    

def delete_jd(id: int):
    """
    根据JD ID删除数据库中对应的JD记录。
    请注意：在运行此函数之前，请确保已经正确配置了数据库连接，并且数据库中已经创建了相应的表结构。
    同时注意设置正确的JD ID，以便函数能够找到并删除对应的JD记录。
    """
    # 首先根据jd_id查询数据库，获取对应的JD记录，确认该记录存在
    # 如果记录存在，则执行DELETE操作删除该记录，并删除该id在向量数据库中对应的记录
    # 删除成功后，返回删除结果或日志信息
    with mysql_engine.connect() as connection:
        result = connection.execute(
            text("""SELECT jd_id FROM tb_jd WHERE id = :id"""),
            {
                "id": id
            }
        )
        record = result.fetchone()  # 获取查询结果
        if record is None:
            logging.error(f"No JD record found with ID: {id}. No deletion performed.")
            return
        jd_id = record.jd_id  # 获取jd_id字段的值
        logging.info(f"Found JD record with ID: {id}, jd_id: {jd_id}. Proceeding with deletion.")
        
        result = connection.execute(
            text("""DELETE FROM tb_jd WHERE id = :id"""),
            {
                "id": id
            }
        )
        connection.commit()  # 提交事务
        if result.rowcount == 0:
            logging.error(f"No JD record found with ID: {id}. No deletion performed.")
        else:
            logging.info(f"Successfully deleted JD record with ID: {id}.")
            # 删除向量数据库中对应的记录
            deleted = resume_vectordb.delete([str(jd_id)])  # 调用resume_vectordb的delete方法，根据ID删除记录
            if deleted:
                logging.info(f"Successfully deleted JD record with JD ID: {jd_id} from vector database.")
            else:
                logging.error(f"Failed to delete JD record with JD ID: {jd_id} from vector database.")


def vectorize_jd_dir(jd_dir: str):
    """
    批量处理JD文件夹中的所有JD文件（只处理一级目录下的文件），提取内容、总结，并添加到向量数据库中。
    请注意：在运行此函数之前，请确保已经正确配置了数据库连接，并且数据库中已经创建了相应的表结构。
    同时注意设置正确的JD文件夹路径，以便函数能够找到并处理该文件夹中的所有JD文件。
    """
    # 遍历jd_dir目录下的所有文件，调用JD_vectorize_node函数处理每个文件
    if not os.path.exists(jd_dir):
        logging.error(f"JD文件夹路径不存在: {jd_dir}")
        return
    
    try:
        for filename in os.listdir(jd_dir):
            file_path = os.path.join(jd_dir, filename)
            if os.path.isfile(file_path):  # 只处理文件，忽略子目录
                if not file_path.lower().endswith(tuple(support_file_types)):
                    logging.error(f"文件 '{file_path}' 格式错误：支持的文件格式为：" + ", ".join(support_file_types))
                    continue
                new_state = state.copy()  # 创建state的副本，避免修改原始state
                new_state["jd_id"] = filename.rsplit('.', 1)[0]  # 使用文件名（不含扩展名）作为JD ID
                new_state["jd_path"] = file_path  # 设置JD文件路径
                new_state["jd_create_time"] = datetime.now()  # 设置创建时间为当前时间
                logging.info(f"Starting to process JD file: {file_path}")
                updated_state = JD_vectorize_node(new_state, config={})  # 调用JD_vectorize_node函数处理文件
                logging.info(f"Finished processing JD file: {file_path}")
                os.remove(file_path)  # 删除处理完成的文件
                sleep(10)  # 添加适当的延迟，避免过快请求API导致限流拒绝响应
    except Exception as e:
        logging.error(f"""Error occurred while processing JD files in directory: {jd_dir}. Error details: {str(e)}
Resumes vectorization process terminated with errors.""")
        
        
def vectorize_jd_from_csv(csv_path: str):
    """
    从CSV文件中批量处理JD文本内容，提取内容、总结，并添加到向量数据库中。
    请注意：在运行此函数之前，请确保已经正确配置了数据库连接，并且数据库中已经创建了相应的表结构。
    同时注意设置正确的CSV文件路径，以便函数能够找到并处理该文件中的JD文本内容。
    CSV内部的属性有：id, jd_id,  job_description, job_title, uid
    """
    # 读取csv文件，获取每行的JD文本内容，调用JD_vectorize_node函数处理每个JD文本内容
    if not os.path.exists(csv_path):
        logging.error(f"CSV文件路径不存在: {csv_path}")
        return
    if not csv_path.lower().endswith('.csv'):
        logging.error(f"文件格式错误：支持的文件格式为CSV。请提供正确的CSV文件路径。")
        return
    try:
        df = read_csv(csv_path)
        for index, row in df.iterrows():
            jd_title = row['job_title']
            jd_desc = row['job_description']
            jd_id = row['jd_id']
            new_state = state.copy()  # 创建state的副本，避免修改原始state
            new_state["jd_id"] = jd_id  # 设置JD ID
            raw_jd_text = "Title:\n" + jd_title + "\nDescription:\n" + jd_desc  # 将职位标题和职位描述合并作为原始JD文本内容
            new_state["raw_jd_text"] = raw_jd_text  # 设置原始JD文本内容
            new_state["jd_create_time"] = datetime.now()  # 设置创建时间为当前时间
            logging.info(f"Starting to process JD with ID: {jd_id}")
            updated_state = JD_vectorize_node(new_state, config={})  # 调用JD_vectorize_node函数处理JD文本内容
            logging.info(f"Finished processing JD with ID: {jd_id}")
            sleep(10)  # 添加适当的延迟，避免过快请求API导致限流拒绝响应
    except Exception as e:
        logging.error(f"""Error occurred while processing JDs from CSV file: {csv_path}. Error details: {str(e)}""")


if __name__ == "__main__":
    # vectorize_jd_dir("/root/program_projects/ResumeSystem/vacancy-resume-matching-dataset/to_vectorize_pdf")
    vectorize_jd_from_csv("/root/program_projects/ResumeSystem/vacancy-resume-matching-dataset/5_vacancies.csv")