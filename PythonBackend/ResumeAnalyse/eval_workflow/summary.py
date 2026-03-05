import logging
import os

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