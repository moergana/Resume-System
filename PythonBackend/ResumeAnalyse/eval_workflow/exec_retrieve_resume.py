from datetime import datetime
import logging
from typing import List

from sqlalchemy import text

from ResumeAnalyse.eval_workflow.commons import mysql_engine
from ResumeAnalyse.eval_workflow.vectorize import retrieve_resumes


def parse_resume_retrieval_to_str(retrieval_result: List[dict]) -> str:
    """
    将检索结果列表转换为字符串格式，方便存储和展示。
    每个检索结果包含简历ID、相关度分数和简历内容等信息。
    """
    result_str = ""
    for idx, item in enumerate(retrieval_result):
        result_str += f"Rank {idx + 1}:\n"
        # result_str += f"Resume ID: {item.get('id', 'N/A')}\n"
        # result_str += f"Similarity Score: {item.get('similarity_score', 'N/A')}\n"
        result_str += f"Resume Content: {item.get('content', 'N/A')}\n\n"
        result_str += "-------------------------\n"
    return result_str


with mysql_engine.connect() as connection:
    result = connection.execute(
        text("""SELECT * FROM tb_jd""")
    )
    jd_rows = result.fetchall()  # 获取所有职位描述的记录
    
    jd_sum = len(jd_rows)   # 获取职位描述记录的总数
    jd_num = 5     # 本次测试打算选取的职位描述记录数量
    
    for j_i in range(min(jd_sum, jd_num)):
        # 选择一条职位描述记录
        jd_record = jd_rows[j_i]
        
        # 根据选中的记录中的jd_id获取职位描述内容
        jd_content = jd_record.summary  # 获取职位描述总结内容
        
        # 调用检索函数从向量数据库中检索相关的简历记录
        retrieved_resumes = retrieve_resumes(JD=jd_content)
        
        # 将检索结果转换为字符串格式
        retrieved_resumes_str = parse_resume_retrieval_to_str(retrieved_resumes)
        
        # 将结构保存到数据库对应的表中
        connection.execute(
            text("""INSERT INTO tb_retrieve_resume (jd_id, retrieve_result, create_time) 
                    VALUES (:jd_id, :retrieve_result, :create_time)"""),
            {
                "jd_id": jd_record.jd_id,
                "retrieve_result": retrieved_resumes_str,
                "create_time": datetime.now()
            }
        )
        connection.commit()  # 提交事务，保存记录到数据库中
        logging.info(f"Retrieved resumes for JD id {jd_record.jd_id} and saved to database successfully.")