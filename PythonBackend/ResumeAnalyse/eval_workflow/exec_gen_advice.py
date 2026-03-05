import logging
from datetime import datetime
from time import sleep

from sqlalchemy import text

from ResumeAnalyse.eval_workflow.analyse import generate_advice, parse_advice_to_str
from ResumeAnalyse.eval_workflow.commons import mysql_engine


with mysql_engine.connect() as connection:
    result = connection.execute(
        text("""SELECT * FROM tb_resume""")
    )
    resume_rows = result.fetchall()  # 获取所有简历的记录
    
    result = connection.execute(
        text("""SELECT * FROM tb_jd""")
    )
    jd_rows = result.fetchall()  # 获取所有JD的记录
    
    resume_sum = len(resume_rows)   # 获取简历记录的总数
    resume_num = 6     # 本次测试打算选取的简历记录数量
    jd_sum = len(jd_rows)   # 获取JD记录的总数
    jd_num = 5      # 本次测试打算选取的JD记录数量
    
    # for r_i in range(min(resume_num, resume_sum)):
    for r_i in range(min(resume_num, resume_sum)):
        for j_i in range(min(jd_num, jd_sum)):
            # 选择一条简历记录和一条JD记录
            resume_record = resume_rows[r_i]
            jd_record = jd_rows[j_i]
            
            # 根据选中的记录中的resume_id和jd_id获取简历内容和JD内容
            resume_content = resume_record.summary  # 获取简历总结内容
            jd_content = jd_record.summary  # 获取JD总结内容
            
            # 调用LLM生成建议分析内容
            logging.info(f"Generating advice for Resume's id: {resume_record.id} and JD's id: {jd_record.id}.")
            advice_content = generate_advice(resume_content, jd_content)
            
            # 将生成的建议分析内容保存到数据库中，假设有一个tb_analysis_advice表用于存储建议分析记录
            logging.info(f"Generated Successfully! Saving advice analysis result to database for r_id: {resume_record.id} and j_id: {jd_record.id}.")
            connection.execute(
                text("""INSERT INTO tb_analysis_advice (r_id, j_id, analysis_result, create_time) 
                        VALUES (:r_id, :j_id, :analysis_result, :create_time)"""),
                {
                    "r_id": resume_record.id,
                    "j_id": jd_record.id,
                    "analysis_result": parse_advice_to_str(advice_content),  # 将Pydantic对象转换为JSON字符串存储
                    "create_time": datetime.now()
                }
            )
            connection.commit()  # 提交事务，保存记录到数据库中
            sleep(60)   # 每次生成建议分析后等待60秒再进行下一次，避免API限流导致测试中止