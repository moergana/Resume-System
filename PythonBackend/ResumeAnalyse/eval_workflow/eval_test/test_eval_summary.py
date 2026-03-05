import os
import logging
from typing import List

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import GEval
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from langchain.chat_models import init_chat_model
from sqlalchemy import text

from ResumeAnalyse.eval_workflow.commons import workspace_root
from ResumeAnalyse.eval_workflow.commons import mysql_engine
from ResumeAnalyse.eval_workflow.eval_test.prompts import *

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

    
def eval_summary(inputs: List[str], summaries: List[str],
                 name: str = "Summary Evaluation",
                 criteria: str = default_summary_criteria,
                 evaluation_steps: List[str] = default_summary_evaluation_steps
                 ) -> float:
    """
    使用DeepEval评估LLM生成的总结内容的质量，输入原始内容和总结内容，输出评估得分。
    """
    # 定义评估总结的指标对象，基于G-Eval算法
    # 设计评估标准和步骤，使用OpenRouter AI作为评估模型，输入参数包括原始内容和总结内容
    summary_metric = GEval(
        name=name,
        criteria=criteria,
        evaluation_steps=evaluation_steps,
        model=openrouter_ai,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT]
    )

    
    # 首先，根据输入参数构造出一个LLMTestCase列表
    test_cases = []
    for input_content, summary in zip(inputs, summaries):
        test_case = LLMTestCase(
            input=input_content,
            actual_output=summary
        )
        test_cases.append(test_case)
        
    # 然后，调用evaluate方法开启一次评估
    # max_concurrent=1: 并发度。当max_concurrent=1时禁止并发，串行逐个评估，避免触发限流
    # throttle_value: 等待时间。每个测试样例评估完成后等待throttle_value秒再执行下一个，避免API限流导致测试中止
    evaluation_result = evaluate(
        test_cases=test_cases,
        metrics=[summary_metric],
        async_config=AsyncConfig(max_concurrent=1, throttle_value=90)
    )
    
    # evaluate() 返回 EvaluationResult 对象，其 .test_results 才是 List[TestResult]
    results = evaluation_result.test_results
    
    # 统计数量
    total_cases = len(results)
    passed_cases = len([r for r in results if r.success])
    failed_cases = total_cases - passed_cases

    print(f"总样例数: {total_cases}")
    print(f"通过数量: {passed_cases}")
    print(f"失败数量: {failed_cases}")
    
    # 最后，计算该次评估的通过率并返回
    return passed_cases / total_cases if total_cases > 0 else 0.0
    

def eval_resume_summary():
    """
    从数据库中获取原始简历内容和预先生成好的简历总结内容，然后调用DeepEval对总结效果进行评估。
    """
    inputs = []
    summaries = []
    with mysql_engine.connect() as connection:
        result = connection.execute(
            text("""SELECT * FROM tb_resume""")
        )
        rows = result.fetchall()  # 获取所有记录
        for row in rows:
            inputs.append(row.raw_text)  # 假设raw_resume_text字段存储了原始内容
            summaries.append(row.summary)  # 假设resume_summary_text字段存储了总结内容
            
    pass_percentage = eval_summary(inputs, summaries,
                                    name="Resume Summary Evaluation",
                                    criteria=resume_summary_criteria,
                                    evaluation_steps=resume_summary_evaluation_steps
                                   )
    print(f"Summary Evaluation Pass Percentage: {pass_percentage:.2%}")
    

def eval_jd_summary():
    """
    从数据库中获取原始JD内容和预先生成好的JD总结内容，然后调用DeepEval对总结效果进行评估。
    """
    inputs = []
    summaries = []
    with mysql_engine.connect() as connection:
        result = connection.execute(
            text("""SELECT * FROM tb_jd""")
        )
        rows = result.fetchall()  # 获取所有记录
        for row in rows:
            inputs.append(row.raw_text)  # 假设raw_jd_text字段存储了原始内容
            summaries.append(row.summary)  # 假设jd_summary_text字段存储了总结内容
            
    pass_percentage = eval_summary(inputs, summaries,
                                    name="JD Summary Evaluation",
                                    criteria=jd_summary_criteria,
                                    evaluation_steps=jd_summary_evaluation_steps
                                   )
    print(f"JD Summary Evaluation Pass Percentage: {pass_percentage:.2%}")
    

# ------------------ 开始评估测试 ------------------
# 从数据库中获取原始内容和预先生成好的总结内容，然后调用DeepEval对总结效果进行评估
eval_resume_summary()
