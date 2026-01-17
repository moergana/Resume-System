import unittest

from ResumeAnalyse.Analyser import generate_advice
from ResumeAnalyse.Vectorizer import handle_dict

# 样例简历内容和职位描述内容
sample_resume = f"""姓名: 项炎
年龄: 37
教育背景: 学校: 北京科技经营管理学院; 学位: 学士学位; 毕业年份: 2010.06
工作经验: 2007.03-2010.07：广州云蝶科技有限公司，产品开发，负责Unity场景搭建、灯光渲染、性能优化等工作; 2005.04-2018.04：前程无忧（长沙），试剂生产员（生物），负责行政支持、物资管理、档案整理等工作; 1990.06-2016.12：T3出行，诉讼部诉讼秘书，负责运营文件起草、制度监控、销售报表分析等工作; 2007.06-2017.02：嘉展国际，财务业务员，负责医药产品招商推广、市场规划、代理商管理等工作
项目经历: 2000.04-2011.04：信息化条件下宣传思想工作研究，负责多媒体运营渠道拓展、广告资源整合等工作; 2006.05-2013.12：自媒体时代主流意识形态话语面临的挑战及对策研究，协调拍摄资源、解决拍摄问题等工作; 2006.01-2010.10：岭南文化融入大学生思想政治教育研究，负责台账管理、客户资料归档、人事工作等
专业技能: Unity场景搭建与渲染; 游戏性能优化; 行政管理与协调; 市场推广与销售; 多媒体运营与广告投放; 项目协调与资源管理
求职目标: 前端开发
相关证书: 未提供
综合素质总结: 项炎拥有3年工作经验，学士学位，擅长Unity开发、行政管理、市场推广等多领域工作。在前端开发领域有明确的职业目标，具备较强的项目协调和资源管理能力。
"""

sample_jd = f"""职位名称: "前端开发工程师"
公司名称: "Tech Innovators Ltd."
工作地点: "北京"
职位职责: 负责公司网站和应用的前端开发与维护; 与设计团队合作，实现高质量的用户界面; 优化网站性能，提升用户体验; 参与需求分析和技术方案制定
职位要求: 熟悉JavaScript、HTML、CSS等前端技术; 有React或Vue.js等主流框架的开发经验; 具备良好的代码编写习惯和团队合作精神; 有相关项目经验者优先考虑
职位福利: 具有竞争力的薪资待遇; 弹性工作时间和远程办公选项; 完善的培训和职业发展机会; 丰富的员工活动和团队建设活动
职位描述总结: Tech Innovators Ltd.正在北京招聘一位经验丰富的前端开发工程师，负责网站和应用的前端开发与维护，
要求熟悉JavaScript、HTML、CSS等前端技术，并有React或Vue.js等框架的开发经验。
公司提供具有竞争力的薪资待遇、弹性工作时间、远程办公选项以及完善的培训和职业发展机会。
"""


class AdviserTestCase(unittest.TestCase):
    def test_something(self):
        d = {
            "a": 1,
            "b": "wserzsd",
        }
        print(d)
        formatted_d = handle_dict(d)
        print(formatted_d)

    def test_adviser(self):
        advice = generate_advice(sample_resume, sample_jd)
        print("Match Score:", advice.match_score)
        print("Improvement Suggestions:", advice.improvement_suggestions)
        print("Job Hunting Tips:", advice.job_hunting_tips)


if __name__ == '__main__':
    unittest.main()
