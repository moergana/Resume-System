from typing import List, Dict, TypedDict, Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class ResumeSummary(BaseModel):
    """
    对从简历PDF文件中提取得到的Markdown文本信息提取出多种关键信息的类
    """
    name: str = Field(default="", description="应聘者的姓名。")
    age: int = Field(default=-1, description="应聘者的年龄。")
    education: Dict[str, str] = Field(default={},
                                      description="""应聘者的教育背景。应当包含学校名称、学位和毕业年份等信息。以字典结构返回。""")
    experience: List[str] = Field(default=[], description="""应聘者的工作经验。
    可能包含有多段工作经历，每段经历应包含公司名称、职位、工作时间和主要职责等信息。
    以列表结构返回，每个元素为一段工作经历的描述。""")
    projects: List[str] = Field(default=[], description="""应聘者参与过的项目经历。
    可能包含有多段项目经历，每段经历应包含项目名称、时间和主要内容等信息。
    以列表结构返回，每个元素为一段项目经历的描述。""")
    skills: List[str] = Field(default=[], description="""应聘者具有的专业技能。可能包含有多个技能，结果以列表结构返回。""")
    target: str = Field(default="", description="应聘者的求职目标或意向职位。")
    certifications: List[str] = Field(default=[],
                                      description="应聘者获得的相关证书或资格。可能包含有多个证书，结果以列表结构返回。")
    summary: str = Field(default="", description="综上所有信息，对于应聘者综合素质的全面且精炼的总结。")


class JDSummary(BaseModel):
    """
    对从职位描述(JD)文本中提取的关键信息进行结构化表示的类
    """
    title: str = Field(default="", description="职位名称。")
    company: str = Field(default="", description="招聘公司名称。")
    location: str = Field(default="", description="工作地点。")
    responsibilities: List[str] = Field(default=[], description="职位职责列表。")
    requirements: List[str] = Field(default=[], description="职位要求列表。")
    benefits: List[str] = Field(default=[], description="职位福利列表。")
    summary: str = Field(default="", description="对职位描述的综合总结。")
