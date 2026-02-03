import os
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from langgraph.types import Command
from pydantic import BaseModel, Field

from ResumeAnalyse import utils
from ResumeAnalyse.entity.advice import Advice
from ResumeAnalyse.entity.difference import Difference

Model_Name = "mistralai/mistral-small-3.1-24b-instruct:free"
Base_URL = "https://openrouter.ai/api/v1"
analyser_llm = init_chat_model(
    model=Model_Name,
    base_url=Base_URL,
    model_provider="openai",
    api_key=utils.openrouter_api_key,
)


difference_prompt_template = PromptTemplate.from_template(
    """你是一个优秀的人力资源专家，擅长于分析和解答与简历和职位描述相关的问题。
    现在有一份简历和一份职位描述，你需要分析这份简历与职位描述的匹配度并给出匹配度分数（百分制，范围0~100，分数越高表示匹配度越高），
    并结合简历与职位描述的信息，面向招聘者给出关于简历与职位描述的差异点分析，比如哪些方面不匹配，存在哪些不足等，以辅助招聘决策。
    简历内容如下：
    {resume_content}
    职位描述内容如下：
    {jd_content}"""
)


def generate_difference(resume_content: str, jd_content: str) -> Difference:
    """
    （该功能面向招聘者）
    根据简历内容和职位描述内容，生成简历与职位的匹配度和具体差异点
    :param resume_content: 简历内容
    :param jd_content: 职位描述
    :return: Difference对象，包含匹配度分数、差异点分析
    """
    structured_adviser_llm = analyser_llm.with_structured_output(Difference)
    response = structured_adviser_llm.invoke(
        input=[
            HumanMessage(content=difference_prompt_template.format(resume_content=resume_content, jd_content=jd_content))]
    )  # 返回的内容会被自动解析为BaseModel类型的Difference对象
    """
    # 如果LLM不支持with_structured_output方法，可以使用bind_tools方法结合Tool来实现结构化输出
    structured_adviser_llm = adviser_llm.bind_tools([Difference])
    response = structured_adviser_llm.invoke(
        input=[
            HumanMessage(content=adviser_prompt_template.format(resume_content=resume_content, jd_content=jd_content))]
    )
    # invoke返回的response是一个AIMessage对象，包含了工具调用的记录
    difference = response.tool_calls[-1]['args']  # 从工具调用的参数中获取结构化输出结果，是一个dict类型对象
    difference = BaseModel(**advice)  # 将dict转换为Advise对象
    """
    # 将BaseModel类型的response转换为Difference对象并返回
    return Difference.model_validate(response)


advice_prompt_template = PromptTemplate.from_template(
    """你是一个优秀的人力资源专家，擅长于分析和解答与简历和职位描述相关的问题。
    现在有一份简历和一份职位描述，你需要分析这份简历与职位描述的匹配度并给出匹配度分数（百分制，范围0~100，分数越高表示匹配度越高）。
    同时，结合简历与职位描述的信息，面向求职者给出合理的简历改进建议以及求职建议。
    简历内容如下：
    {resume_content}
    职位描述内容如下：
    {jd_content}"""
)


def generate_advice(resume_content: str, jd_content: str) -> Advice:
    """
    （该功能面向求职者）
    根据简历内容和职位描述内容，生成简历与职位的匹配度和改进建议
    :param resume_content: 简历内容
    :param jd_content: 职位描述
    :return: Advise对象，包含匹配度分数、改进建议和求职建议
    """
    structured_adviser_llm = analyser_llm.with_structured_output(Advice)
    response = structured_adviser_llm.invoke(
        input=[
            HumanMessage(content=advice_prompt_template.format(resume_content=resume_content, jd_content=jd_content))]
    )  # 返回的内容会被自动解析为BaseModel类型的Advice对象
    """
    # 如果LLM不支持with_structured_output方法，可以使用bind_tools方法结合Tool来实现结构化输出
    structured_adviser_llm = adviser_llm.bind_tools([Advise])
    response = structured_adviser_llm.invoke(
        input=[
            HumanMessage(content=adviser_prompt_template.format(resume_content=resume_content, jd_content=jd_content))]
    )
    # invoke返回的response是一个AIMessage对象，包含了工具调用的记录
    advice = response.tool_calls[-1]['args']  # 从工具调用的参数中获取结构化输出结果，是一个dict类型对象
    advice = BaseModel(**advice)  # 将dict转换为Advise对象
    """
    # 将BaseModel类型的response转换为Advice对象并返回
    return Advice.model_validate(response)


if __name__ == "__main__":
    # 测试代码
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

    advice = generate_advice(sample_resume, sample_jd)
    print("Match Score:", advice.match_score)
    print("Improvement Suggestions:", advice.improvement_suggestions)
    print("Job Hunting Tips:", advice.job_hunting_tips)
