import os

from deepeval import assert_test
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import Turn, ConversationalTestCase
from deepeval.metrics import ConversationalGEval
from langchain.chat_models import init_chat_model


class OpenRouterAI(DeepEvalBaseLLM):
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

def test_professionalism():
    professionalism_metric = ConversationalGEval(
        name="Professionalism",
        model=openrouter_ai,
        criteria="Determine whether the assistant has acted professionally based on the content.",
        threshold=0.5
    )
    test_case = ConversationalTestCase(
        turns=[
            Turn(role="user", content="What is DeepEval?"),
            Turn(role="assistant", content="DeepEval is an open-source LLM eval package.")
        ]
    )
    assert_test(test_case, [professionalism_metric])