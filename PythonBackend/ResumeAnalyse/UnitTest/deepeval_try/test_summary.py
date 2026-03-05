import json
import logging
import os

# ── Monkey-patch: 修复 deepeval 写入测试结果时中文被转义为 \uXXXX 的问题 ──
#（注意：该方式是通过运行时动态修改代码实现，如果其他文件也需要修改，都需要引入该代码块）
# deepeval 内部的 json.dump 调用默认 ensure_ascii=True，
# 此处在模块级别覆盖 deepeval.test_run.test_run 模块的 json.dump，
# 使其默认以 ensure_ascii=False 写出（即保留原始 UTF-8 字符）。
import deepeval.test_run.test_run as _trt

_original_json_dump = json.dump

def _utf8_json_dump(obj, fp, **kwargs):
    kwargs.setdefault("ensure_ascii", False)    # 设置 ensure_ascii=False，保留原始 UTF-8 字符而不是转义为 \uXXXX
    kwargs.setdefault("indent", 2)  # 可选：添加缩进使输出更美观
    return _original_json_dump(obj, fp, **kwargs)

_trt.json.dump = _utf8_json_dump  # 仅作用于该模块命名空间，不影响其他代码
# ─────────────────────────────────────────────────────────────────────────────
# 如果需要一劳永逸的解决该问题，建议直接修改 deepeval.test_run.test_run 的源代码，将 json.dump 的调用改为默认 ensure_ascii=False
# ─────────────────────────────────────────────────────────────────────────────

from deepeval import evaluate
from deepeval.metrics import GEval, SummarizationMetric
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, LLMTestCaseParams, LLMTestCaseParams
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate

from ResumeAnalyse.entity.summary import JDSummary, ResumeSummary


openrouter_api_key = os.getenv("OPENROUTER_KEY")
assert openrouter_api_key, "请先在系统环境变量中设置 OPENROUTER_KEY！"


Model_Name = "openrouter/free"
Base_URL = "https://openrouter.ai/api/v1"
summary_llm = init_chat_model(
    model=Model_Name,
    base_url=Base_URL,
    model_provider="openai",
    api_key=openrouter_api_key,
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
如果某些信息在简历中没有明确提及而无法确定，请相应地标注为“未知”或“未提供”等提示信息。
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
如果某些信息在职位描述中没有明确提及而无法确定，请相应地标注为“未知”或“未提供”等提示信息。
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


class OpenRouterAI(DeepEvalBaseLLM):
    """
    A custom LLM wrapper for OpenRouter AI to be used with DeepEval.
    This class implements the necessary methods to interface with DeepEval's evaluation framework.
    It uses the LangChain chat model interface to interact with the OpenRouter API.
    如果不使用DeepEval默认的gpt-4.1，可以通过指定其他模型的名称，或者自己实现DeepEvalBaseLLM的子类来调用其他LLM模型评估。
    """
    def __init__(
        self,
        model
    ):
        self.model = model

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        chat_model = self.load_model()
        return chat_model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        chat_model = self.load_model()
        res = await chat_model.ainvoke(prompt)
        return res.content

    def get_model_name(self):
        return "Custom OpenRouter AI Model"


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

""" 
resume_summary = resume_summarize(resume_markdown_res)
JD_summary = JD_summarize(JD_markdown_res)

resume_summary_str = resume_summary.model_dump_json()
JD_summary_str = JD_summary.model_dump_json()

print("Resume Summary:", resume_summary_str)
print("JD Summary:", JD_summary_str) 
"""

resume_summary_str = '''{"name":"项炎","age":37,"education":{"degree":"学士学位","institution":"北京科技经营管理学院","period":"2006.06 -- 2010.06"},"experience":["广州云蝶科技有限公司 (2007.03-2010.07) - 产品开发","前程无忧 (2005.04-2018.04) - 试剂生产员","T3 出行 (1990.06-2016.12) - 诉讼部诉讼秘书","嘉展国际 (2007.06-2017.02) - 财务业务员"],"projects":["信息化条件下宣传思想工作研究 (2000.04-2011.04)","自媒体时代主流意识形态话语面临的挑战及对策研究 (2006.05-2013.12)","岭南文化融入大学生思想政治教育研究 (2006.01-2010.10)"],"skills":["Unity","场景搭建","灯光渲染","场景性能优化","材质调整","场景性能把控","场景制作计划","场景任务分配","场景协调配合","行政事务处理","档案管理","资产管理","供应商对账","采购管理","信息系统管理","招商推广","市场信息收集","代理商网络拓展","微观管理","招标处理","纪录片拍摄","拍摄资源协调","拍摄困难解决","台账制作","客户资料归档","签约贷后","办公用品采购","租房合同管理","人事相关工作"],"target":"前端开发","certifications":["未提供"],"summary":"项炎，37岁，江西景德镇籍，拥有3年前端开发经验。教育背景：北京科技经营管理学院学士学位。工作经历包括产品开发、行政事务、诉讼秘书、财务业务员等。专业技能涵盖Unity场景搭建、性能优化、行政事务处理等。求职目标：前端开发。项目经验包括信息化宣传研究、自媒体意识形态挑战研究等。 Certifications: 未提供。"}'''
JD_summary_str = '''{"title":"前端开发工程师","company":"Tech Innovators Ltd.","location":"北京","responsibilities":["负责公司网站和应用的前端开发与维护","与设计团队合作，实现高质量的用户界面","优化网站性能，提升用户体验","参与需求分析和技术方案制定"],"requirements":["熟悉JavaScript、HTML、CSS等前端技术","有React或Vue.js等主流框架的开发经验","具备良好的代码编写习惯和团队合作精神","有相关项目经验者优先考虑"],"benefits":["具有竞争力的薪资待遇","弹性工作时间和远程办公选项","完善的培训和职业发展机会","丰富的员工活动和团队建设活动"],"summary":"Tech Innovators Ltd. 在北京招聘经验丰富的前端开发工程师，需具备JavaScript/H5技术栈基础，熟悉React/Vue等主流框架开发经验，强调代码规范与团队协作能力。职位涵盖前端开发部署、UI交付、性能优化及需求分析，提供具竞争力的薪酬、弹性工作、培训机会及丰富团队活动等福利。适合有项目经验的高级前端工程师加入。"}'''

resume_summary_test_case = LLMTestCase(input=resume_markdown_res, actual_output=resume_summary_str)
JD_summary_test_case = LLMTestCase(input=JD_markdown_res, actual_output=JD_summary_str)

openrouter_ai = OpenRouterAI(model=summary_llm)

# 定义评估指标，使用SummarizationMetric来评估生成的摘要与实际摘要之间的相似度
# 但是SummarizationMetric封装的比较简单且死板，使用泛用性更强的G-Eval也能够完成总结能力评估，且自定义灵活度更高。
""" 
metric = SummarizationMetric(
    threshold=0.5,
    model=openrouter_ai,
    verbose_mode=True   # verbose_mode=True会在评估过程中输出中间步骤的结果
) 
"""

metric = GEval(
    name="Summary Evaluation",
    criteria="请根据input提供的内容，判断actual_output是否是对input的准确、全面且精炼的总结。",
    evaluation_steps=[
        "准确性：actual_output是否准确反映了input中的关键信息？",
        "全面性：actual_output是否涵盖了input中的主要内容和重要细节？",
        "精炼性：actual_output是否用简洁的语言表达了input的核心内容，避免冗余信息？",
        "忠实性：actual_output是否忠实于input的内容，有没有添加与input不符的信息或者自己编造信息？",
        "格式问题：不要关注input和actual_output的格式差异，只需要专注于二者的核心内容。对于JSON格式，需要将字段名和字段值的含义结合起来理解，而不是仅仅关注字段值内容的匹配程度。"
        "即便actual_output中出现了不合逻辑或者自相矛盾的表达，也不要因此降低对actual_output的评分，一切以input的内容为准。"
        "只要actual_output整体上能够准确、全面、精炼且忠实地总结input的内容，就可以给予高评分。"
    ],
    model=openrouter_ai,
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT]
)

evaluate(
    test_cases=[resume_summary_test_case, JD_summary_test_case],
    metrics=[metric]
)
