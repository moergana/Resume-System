import logging
import unittest

from ResumeAnalyse.constants import *
from ResumeAnalyse.entity.state import GraphState
from ResumeAnalyse.Workflow import graph_executor
import json


class WorkflowTestCase(unittest.TestCase):
    def test_resume_advise(self):
        initial_state: GraphState = {
            "messages": [],

            "user_id": "test_user",
            "request_type": REQUEST_RESUME_ADVISE,

            "resume_path": "/root/program_projects/LangGraph/Resume_Data/sample/resume_sample_20200120/pdf/31b40b91486b.pdf",
            "jd_path": "",
            "resume_id": "resume_test_1",
            "jd_id": "JD_test_1",
            "resume_summary_text": "",
            "jd_summary_text": f"""职位名称: "前端开发工程师"
公司名称: "Tech Innovators Ltd."
工作地点: "北京"
职位职责: 负责公司网站和应用的前端开发与维护; 与设计团队合作，实现高质量的用户界面; 优化网站性能，提升用户体验; 参与需求分析和技术方案制定
职位要求: 熟悉JavaScript、HTML、CSS等前端技术; 有React或Vue.js等主流框架的开发经验; 具备良好的代码编写习惯和团队合作精神; 有相关项目经验者优先考虑
职位福利: 具有竞争力的薪资待遇; 弹性工作时间和远程办公选项; 完善的培训和职业发展机会; 丰富的员工活动和团队建设活动
职位描述总结: Tech Innovators Ltd.正在北京招聘一位经验丰富的前端开发工程师，负责网站和应用的前端开发与维护，
要求熟悉JavaScript、HTML、CSS等前端技术，并有React或Vue.js等框架的开发经验。
公司提供具有竞争力的薪资待遇、弹性工作时间、远程办公选项以及完善的培训和职业发展机会。
""",

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
        print("Final State Type:", type(final_state))
        # 将final_state转为JSON字符串并打印
        # ensure_ascii=False用于正确显示中文字符，indent=2用于美化输出格式
        print("Final State JSON:", json.dumps(final_state, ensure_ascii=False, indent=2))

    def test_jd_match(self):
        initial_state: GraphState = {
            "messages": [],

            "user_id": "test_user",
            "request_type": REQUEST_JD_MATCH,

            "resume_path": "/root/program_projects/LangGraph/Resume_Data/sample/resume_sample_20200120/pdf/31b40b91486b.pdf",
            "jd_path": "",
            "resume_id": "resume_test_1",
            "jd_id": "",
            "resume_summary_text": "",
            "jd_summary_text": f"""""",

            "match_score": -1,
            "differences": "",
            "improvement_suggestions": "",
            "job_hunting_tips": "",

            "retrieved_resumes": [],
            "retrieved_jds": [],

            "status": "",
            "log_msg": [],
        }
        print(f"initial_state(JSON):\n{json.dumps(initial_state, ensure_ascii=False, indent=2)}\n")
        final_state = graph_executor.invoke(initial_state)
        print("Final State Type:", type(final_state))
        # 将final_state转为JSON字符串并打印
        # ensure_ascii=False用于正确显示中文字符，indent=2用于美化输出格式
        print("Final State JSON:", json.dumps(final_state, ensure_ascii=False, indent=2))

    def test_resume_match(self):
        initial_state: GraphState = {
            "messages": [],

            "user_id": "test_user",
            "request_type": REQUEST_RESUME_MATCH,

            "resume_path": "",
            "jd_path": "",
            "resume_id": "",
            "jd_id": "JD_test_1",
            "resume_summary_text": "",
            "jd_summary_text": f"""职位名称: 前端开发工程师
公司名称: Tech Innovators Ltd.
工作地点: 北京
职位职责: 负责公司网站和应用的前端开发与维护; 与设计团队合作，实现高质量的用户界面; 优化网站性能，提升用户体验; 参与需求分析和技术方案制定
职位要求: 熟悉JavaScript、HTML、CSS等前端技术; 有React或Vue.js等主流框架的开发经验; 具备良好的代码编写习惯和团队合作精神; 有相关项目经验者优先考虑
职位福利: 具有竞争力的薪资待遇; 弹性工作时间和远程办公选项; 完善的培训和职业发展机会; 丰富的员工活动和团队建设活动
职位描述总结: Tech Innovators Ltd.正在北京招聘一位经验丰富的前端开发工程师，负责网站和应用的前端开发与维护，
要求熟悉JavaScript、HTML、CSS等前端技术，并有React或Vue.js等框架的开发经验。
公司提供具有竞争力的薪资待遇、弹性工作时间、远程办公选项以及完善的培训和职业发展机会。
""",

            "match_score": -1,
            "differences": "",
            "improvement_suggestions": "",
            "job_hunting_tips": "",

            "retrieved_resumes": [],
            "retrieved_jds": [],

            "status": "",
            "log_msg": [],
        }
        print(f"initial_state(JSON):\n{json.dumps(initial_state, ensure_ascii=False, indent=2)}\n")
        final_state = graph_executor.invoke(initial_state)
        print("Final State Type:", type(final_state))
        # 将final_state转为JSON字符串并打印
        # ensure_ascii=False用于正确显示中文字符，indent=2用于美化输出格式
        print("Final State JSON:", json.dumps(final_state, ensure_ascii=False, indent=2))

        """
{
  "messages": [],
  "user_id": "test_user",
  "request_type": "resume_match",
  "resume_path": "",
  "jd_path": "",
  "resume_id": "",
  "jd_id": "JD_test_1",
  "resume_summary_text": "",
  "jd_summary_text": "职位名称: 前端开发工程师
  公司名称: Tech Innovators Ltd.
  工作地点: 北京
  薪资: 10000-15000元/月
  职位职责: 负责公司网站和应用的前端开发与维护; 与设计团队合作，实现高质量的用户界面; 优化网站性能，提升用户体验; 参与需求分析和技术方案制定
  职位要求: 熟悉JavaScript、HTML、CSS等前端技术; 有React或Vue.js等主流框架的开发经验; 具备良好的代码编写习惯和团队合作精神; 有相关项目经验者优先考虑
  职位福利: 具有竞争力的薪资待遇; 弹性工作时间和远程办公选项; 完善的培训和职业发展机会; 丰富的员工活动和团队建设活动
  职位描述总结: Tech Innovators Ltd.正在北京招聘一位经验丰富的前端开发工程师，负责网站和应用的前端开发与维护，要求熟悉JavaScript、HTML、CSS等前端技术，并有React或Vue.js等框架的开发经验。
  公司提供具有竞争力的薪资待遇、弹性工作时间、远程办公选项以及完善的培训和职业发展机会。",
  "match_score": -1,
  "differences": "",
  "improvement_suggestions": "",
  "job_hunting_tips": "",
  "retrieved_resumes": [],
  "retrieved_jds": [],
  "state": "",
  "log_msg": []
}
        """
        

if __name__ == '__main__':
    unittest.main()
