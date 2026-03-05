import os
from langchain.chat_models import init_chat_model
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval


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

openrouter_ai = OpenRouterAI(model=summary_llm)

def test_correctness():
    correctness_metric = GEval(
        name="Correctness",
        model=openrouter_ai,
        criteria="Determine if the 'actual output' is correct based on the 'expected output'.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.5
    )
    test_case = LLMTestCase(
        input="I have a persistent cough and fever. Should I be worried?",
        # Replace this with the actual output from your LLM application
        actual_output="A persistent cough and fever could be a viral infection or something more serious. See a doctor if symptoms worsen or don't improve in a few days.",
        expected_output="A persistent cough and fever could indicate a range of illnesses, from a mild viral infection to more serious conditions like pneumonia or COVID-19. You should seek medical attention if your symptoms worsen, persist for more than a few days, or are accompanied by difficulty breathing, chest pain, or other concerning signs."
    )
    assert_test(test_case, [correctness_metric])