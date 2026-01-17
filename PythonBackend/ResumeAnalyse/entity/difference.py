from pydantic import BaseModel, Field


class Difference(BaseModel):
    match_score: int = Field(..., description="简历与职位描述的匹配度分数，百分制，范围0~100，分数越高表示匹配度越高。")
    differences: str = Field(..., description="""简历与职位描述之间的具体差异点，比如某项技能的缺失，某个项目与职位不匹配等。
你可以选择以清单形式列出回答，同时注意在必要的地方换行，提升用户的阅读体验。
另外，你可以适当使用基础的markdown语法来增强可读性，例如使用粗体、斜体等格式。""")
