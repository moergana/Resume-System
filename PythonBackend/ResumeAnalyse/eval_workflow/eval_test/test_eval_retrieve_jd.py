from typing import List

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import GEval
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from langchain.chat_models import init_chat_model
from sqlalchemy import text

from ResumeAnalyse.eval_workflow.commons import mysql_engine
from ResumeAnalyse.eval_workflow.commons import openrouter_api_key, openrouter_api_key_2
from ResumeAnalyse.eval_workflow.eval_test.prompts import *


with mysql_engine.connect() as connection:
    result = connection.execute(
        text("""SELECT tb_resume.summary as resume_summary, tb_retrieve_jd.retrieve_result as retrieve_result
             FROM tb_retrieve_jd join tb_resume ON tb_retrieve_jd.resume_id = tb_resume.resume_id
             where tb_retrieve_jd.id = 11""")
    )
    resume_rows = result.fetchall()  # 获取所有简历的记录
    
    # 构建LLMTestCase列表
    test_cases = []
    for resume_record in resume_rows:
        test_case = LLMTestCase(
            input=resume_record.resume_summary,  # 输入是简历的摘要
            actual_output=resume_record.retrieve_result  # 实际输出是检索结果
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


def eval_retrieve_jd(test_cases: List[LLMTestCase],
                      name: str = "Retrieve JD Evaluation",
                      criteria: str = default_retrieve_jd_criteria,
                      evaluate_steps: List[str] = default_retrieve_jd_evaluation_steps):
    """
    评估函数，比较指定的JD内容与检索结果的匹配度
    :param test_case: LLMTestCase对象，包含输入和预期输出
    """
    # 定义评估指标对象，基于G-Eval算法
    # 设计评估标准和步骤，使用OpenRouter AI作为评估模型，输入参数包括原始内容和总结内容
    retrieve_jd_metric = GEval(
        name=name,
        criteria=criteria,
        evaluation_steps=evaluate_steps,
        model=openrouter_ai,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT]
    )
    
    # 执行评估，输入参数包括JD内容和检索结果字符串
    # max_concurrent=1: 并发度。当max_concurrent=1时禁止并发，串行逐个评估，避免触发限流
    # throttle_value: 等待时间。每个测试样例评估完成后等待throttle_value秒再执行下一个，避免API限流导致测试中止
    evaluate(
        test_cases=test_cases,
        metrics=[retrieve_jd_metric],
        async_config=AsyncConfig(max_concurrent=1, throttle_value=60)
    )
    
    
# ------------------ 开始评估测试 ------------------
eval_retrieve_jd(test_cases=test_cases)