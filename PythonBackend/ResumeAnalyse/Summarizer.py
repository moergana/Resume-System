import logging

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from pydantic import Field, BaseModel
from typing import List, Dict

from ResumeAnalyse import utils
from ResumeAnalyse.entity.summary import ResumeSummary, JDSummary


Model_Name = "openrouter/free"
Base_URL = "https://openrouter.ai/api/v1"
summary_llm = init_chat_model(
    model=Model_Name,
    base_url=Base_URL,
    model_provider="openai",
    api_key=utils.openrouter_api_key,
)


resume_summary_llm_template = PromptTemplate.from_template(template="""你是一名资深的人力资源专家，擅长从简历中提取关键信息。
现在有从简历中提取到的内容信息，请你根据这些简历内容，凝练出以下信息并以JSON的结构化形式返回：
1. 姓名
2. 年龄
3. 教育背景
4. 工作经验
5. 项目经历
6. 专业技能
7. 求职目标或意向职位
8. 相关证书或资格
9. 综合素质总结
请确保提取的信息准确，并将提取到的信息做必要的总结，同时确保总结精炼且保留关键信息。
如果某些信息在简历中没有明确提及而无法确定，请相应地标注为“未知”或“未提供”等提示信息，非文本类型标注为默认值。
简历内容如下：
{resume_content}""")


def resume_summarize(resume: str) -> ResumeSummary:
    resume_summary_llm = summary_llm.with_structured_output(schema=ResumeSummary)
    logging.info("Invoking LLM to generate resume summary.")
    response = resume_summary_llm.invoke(
        input=[HumanMessage(content=resume_summary_llm_template.format(resume_content=resume))]
    )
    summary = response.model_dump_json()  # response已经是Pydantic对象，使用model_dump_json方法转换为JSON字符串

    """
    # 如果LLM不支持with_structured_output方法，可以使用bind_tools方法结合Tool来实现结构化输出
    resume_summary_llm = summary_llm.bind_tools([ResumeSummary])
    response = resume_summary_llm.invoke(
        input=[HumanMessage(content=summary_llm_template.format(resume_content=markdown_res))]
    )
    # invoke返回的response是一个AIMessage对象，包含了工具调用的记录
    summary = response.tool_calls[-1]['args']  # 从工具调用的参数中获取结构化输出结果，是一个dict类型对象
    summary = BaseModel(**summary)  # 将dict转换为ResumeSummary对象
    """
    logging.info("Resume summary generated successfully.")
    logging.debug(f"Generated Resume Summary: {summary}")
    return ResumeSummary.model_validate(response)


jd_summary_llm_template = PromptTemplate.from_template(
    template="""你是一个资深的人力资源专家，擅长从职位描述(JD)中提取关键信息。
现在有一份职位描述(JD)文本，请你根据该职位描述，提取出以下信息并以JSON的结构化形式返回：
1. 职位名称
2. 招聘公司名称
3. 工作地点
4. 职位职责列表
5. 职位要求列表
6. 职位福利列表
7. 对职位描述的综合总结
请确保提取的信息准确，并将提取到的信息做必要的总结，同时确保总结精炼且保留关键信息。
如果某些信息在职位描述中没有明确提及而无法确定，请相应地标注为“未知”或“未提供”等提示信息，非文本类型标注为默认值。
职位描述内容如下：
{jd_content}""")


def JD_summarize(JD: str) -> JDSummary:
    jd_summary_llm = summary_llm.with_structured_output(schema=JDSummary)
    logging.info("Invoking LLM to generate JD summary.")
    response = jd_summary_llm.invoke(
        input=[HumanMessage(content=jd_summary_llm_template.format(jd_content=JD))]
    )
    summary = response.model_dump_json()

    """
    # 如果LLM不支持with_structured_output方法，可以使用bind_tools方法结合Tool来实现结构化输出
    jd_summary_llm = summary_llm.bind_tools([JDSummary])
    response = jd_summary_llm.invoke(
        input=[HumanMessage(content=summary_llm_template.format(jd_content=JD))]
    )
    # invoke返回的response是一个AIMessage对象，包含了工具调用的记录
    summary = response.tool_calls[-1]['args']  # 从工具调用的参数中获取结构化输出结果，是一个dict类型对象
    summary = BaseModel(**summary)  # 将dict转换为JDSummary对象
    """
    logging.info("JD summary generated successfully.")
    logging.debug(f"Generated JD Summary: {summary}")
    return JDSummary.model_validate(response)


if __name__ == "__main__":
    resume_markdown_res = """
    ## 项炎
    意向岗位：前端开发
    出生日期：1987.04
    籍贯：江西省景德镇市
    工作年限：3年
    电话：15707903854
    邮箱：9cxt5f@0355.net
    兴趣爱好
    编程、看电影、音乐
    <!-- image -->
    ## 2006.06 -- 2010.06
    北京科技经营管理学院 学士学位
    工作经历
    <!-- image -->
    ## 2007.03-2010.07
    ## 广州云蝶科技有限公司
    产品开发
    1、负责unity 中场景的搭建和灯光渲染，以及场景所需的效果调整。少量模 型制作修改和材质调整。2、负责游戏场景的性能把控，对不合格的场景进行 调整，和策划程序保持良好沟通3、负责和策划评估场景制作前期计划。4、负 责落实场景主管分配的制作任务，并按质按量完成5、参与场景内部的制作讨 论和分享，和部门同事做好制作内容的协调配合
    ## 2005.04-2018.04 '前程无忧'51job.com（长沙） 试剂生产员（生物）
    1.负责办公室环境的维护、接听转接电话、快递件收发及登记2.协助部门经理 完成行政部各类物资发放、安排配发至各店；3.协助部门经理整理档案，确保 各类档案归档和分类保管工作；4.协助负责行政各类资产（固定资产、小资 产）的库存管理，以便做好管理、统计、盘点等辅助工作；5.协助部门完成各 供应商对账工作；6.每月分店固定采购工作；7.完成上级领导交办的其它事务 性工作。
    ## 1990.06-2016.12
    ## T3 出行
    ## 诉讼部诉讼秘书
    （1）起草各类运营通知文件，召集各类运营会议；（2）对各管理制度、政 策、各项流程的执行进行监控与优化；（3）负责各类销售指标统计报表和报 告的分析，并随时反馈销售异常情况；（4）对各部门工作整体规范性的督导 与跟进；（5）协调各部门运行事宜，跟踪重点工作计划落实；（6）管理优化 公司信息系统；（7）完成总经理交办的其他事宜。
    ## 2007.06-2017.02 嘉展国际
    ## 财务业务员
    1、负责所辖区域内医药产品（聚乙二醇电解质散（II）、肠内营养粉剂 （AA）、红霉素肠溶微丸胶囊）招商推广工作；2、根据公司的销售策略和销 售指标规划所辖市场招商工作，完成年度销售指标；3、收集、整理所辖区域 的的市场信息，并及时应对反馈。4、拓展、稳定和优化代理商网络；5、帮助 代理商做好医院微观管理，提高单位产量，实施精细化招商管理；6、协助处 理招标等政府事务
    ## 项目经历
    ## 2000.04-2011.04
    项目介绍：信息化条件下宣传思想工作研究
    ## 项目内容：
    1、拓展多媒体运营渠道，分析各类投放渠道，根据行业情况确定投放渠道2、 熟悉各类平台的更新和推广规则，根据服务行业的行业规则和公司产品的推广 对象，确定投放平台和投放频率3、整合公司广告资源，投放渠道，区域合伙 人、站长等资源，拓展业务推广渠道及合作空间4、不断物色符合行业特点的 典型代表及典型案例作为宣传视频的素材5、负责与清洁行业、家政服务行业 等相关行业协会、联盟等机构拓展关系、及时了解行业动态，为市场运营提供 最新的行业渠道信息6、领导交办的其他工作
    <!-- image -->
    ## 2006.05-2013.12
    项目介绍：自媒体时代主流意识形态话语面临的挑战及对策研究
    ## 项目内容：
    - 1、了解导演意图，辅助制片人为按期完成纪录片拍摄、制作提供条件；2、协 调影片当地拍摄所需交通、拍摄地等部分资源；3、负责解决拍摄过程中出现 的各种困难，协调各部门之间的工作关系；
    ## 2006.01-2010.10
    项目介绍：岭南文化融入大学生思想政治教育研究
    ## 项目内容：
    - 1．负责分公司台账制作、管理；2．及时将客户资料归档保存；3．协助客户 经理签约及贷后相关事宜；4．负责办公用品、文具、劳保福利用品的采购、 登记和发放工作；5．负责总部及分公司租房合同管理及房租、水电费用等结 算；6．招聘、入离职办理及社保公积金购买等人事相关工作；7．完成分公司 负责人交代的其他工作任务。
    """
    JD_markdown_res = """
    招聘前端开发工程师
    ## 工作地点：北京
    ## 公司名称：Tech Innovators Ltd.
    ## 职位描述：
    我们正在寻找一位经验丰富的前端开发工程师加入我们的团队。
    主要职责包括：
    - 负责公司网站和应用的前端开发与维护
    - 与设计团队合作，实现高质量的用户界面
    - 优化网站性能，提升用户体验
    - 参与需求分析和技术方案制定
    ## 职位要求：
    - 熟悉JavaScript、HTML、CSS等前端技术
    - 有React或Vue.js等主流框架的开发经验
    - 具备良好的代码编写习惯和团队合作精神
    - 有相关项目经验者优先考虑
    ## 福利待遇：
    - 具有竞争力的薪资待遇
    - 弹性工作时间和远程办公选项
    - 完善的培训和职业发展机会
    - 丰富的员工活动和团队建设活动
    """

    resume_summary = resume_summarize(resume_markdown_res)
    JD_summary = JD_summarize(JD_markdown_res)

    print("Resume Summary:", resume_summary.model_dump_json())
    print("JD Summary:", JD_summary.model_dump_json())
