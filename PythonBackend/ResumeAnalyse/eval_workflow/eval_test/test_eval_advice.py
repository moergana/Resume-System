from typing import List

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import GEval
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from langchain.chat_models import init_chat_model
from langchain_classic.prompts import PromptTemplate
from sqlalchemy import text

from ResumeAnalyse.eval_workflow.commons import mysql_engine
from ResumeAnalyse.eval_workflow.commons import openrouter_api_key, openrouter_api_key_2
from ResumeAnalyse.eval_workflow.eval_test.prompts import *

with mysql_engine.connect() as connection:
    result = connection.execute(
        text("""SELECT tb_resume.summary as resume_summary, tb_jd.summary as jd_summary, tb_analysis_advice.analysis_result as advice_result
             From tb_analysis_advice join tb_resume on tb_analysis_advice.r_id = tb_resume.id
             join tb_jd on tb_analysis_advice.j_id = tb_jd.id""")
    )
    analysis_rows = result.fetchall()  # 获取所有建议分析的记录
    
    input_template = PromptTemplate.from_template(
        """简历内容如下：{resume_content}
职位描述内容如下：{jd_content}"""
    )
    
    # 构建LLMTestCase列表
    test_cases = []
    for row in analysis_rows:
        resume_content = row.resume_summary
        jd_content = row.jd_summary
        advice_result = row.advice_result
        
        test_case = LLMTestCase(
            input=input_template.format(resume_content=resume_content, jd_content=jd_content),
            actual_output=advice_result
        )
        test_cases.append(test_case)
        

Model_Name = "openrouter/free"
Base_URL = "https://openrouter.ai/api/v1"
summary_llm = init_chat_model(
    model=Model_Name,
    base_url=Base_URL,
    model_provider="openai",
    api_key=openrouter_api_key_2,
)


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


openrouter_ai = OpenRouterAI(model=summary_llm)


def eval_advice(test_cases: List[LLMTestCase],
                 name: str = "Advice Evaluation",
                 criteria: str = advice_criteria,
                 evaluation_steps: List[str] = advice_evaluation_steps
                 ) -> float:
    """
    使用DeepEval评估LLM生成的建议内容的质量，输入原始内容和建议内容，输出评估得分。
    """
    # 定义评估总结的指标对象，基于G-Eval算法
    # 设计评估标准和步骤，使用OpenRouter AI作为评估模型，输入参数包括原始内容和总结内容
    advice_metric = GEval(
        name=name,
        criteria=criteria,
        evaluation_steps=evaluation_steps,
        model=openrouter_ai,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT]
    )
        
    # 然后，调用evaluate方法开启一次评估
    # max_concurrent=1: 并发度。当max_concurrent=1时禁止并发，串行逐个评估，避免触发限流
    # throttle_value: 等待时间。每个测试样例评估完成后等待throttle_value秒再执行下一个，避免API限流导致测试中止
    evaluate(
        test_cases=test_cases,
        metrics=[advice_metric],
        async_config=AsyncConfig(max_concurrent=1, throttle_value=60)
    )
    

# ------------------ 开始评估测试 ------------------
eval_advice(test_cases=test_cases)