from pydantic import Field, BaseModel


class Advice(BaseModel):
    match_score: int = Field(..., description="简历与职位描述的匹配度分数，百分制，范围0~100，分数越高表示匹配度越高。")
    improvement_suggestions: str = Field(..., description="""结合简历与职位描述的信息，针对当前简历的改进建议。
你可以选择以清单形式列出回答，同时注意在必要的地方换行，提升用户的阅读体验。
另外，你可以适当使用基础的markdown语法来增强可读性，例如使用粗体、斜体等格式。""")
    job_hunting_tips: str = Field(..., description="""结合简历与职位描述的信息，针对后续求职的建议。
你可以选择以清单形式列出回答，同时注意在必要的地方换行，提升用户的阅读体验。
另外，你可以适当使用基础的markdown语法来增强可读性，例如使用粗体、斜体等格式。""")
