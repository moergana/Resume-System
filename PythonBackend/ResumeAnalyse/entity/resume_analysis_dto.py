from datetime import datetime

from pydantic import BaseModel, Field


class ResumeAnalysisDTO(BaseModel):
    """
    简历分析数据传输对象
    用于和Java端进行数据交互
    """
    id: int = Field(default=0, description="主键ID")

    userId: int = Field(default=0, description="用户ID")

    requestType: str = Field(default="", description="请求类型（resume_upload：上传简历，jd_upload：上传JD，resume_advise：分析简历与建议）")

    resumeId: int = Field(default=0, description="简历ID")

    resumeFilePath: str = Field(default="", description="简历文件路径")

    jdID: int = Field(default=0, description="JD ID")

    title: str = Field(default="", description="职位标题")

    company: str = Field(default="", description="公司名称")

    location: str = Field(default="", description="工作地点")

    salary: str = Field(default="", description="薪资")

    description: str = Field(default="", description="职位描述")

    requirements: str = Field(default="", description="职位要求")

    bonus: str = Field(default="", description="职位福利")

    jdFilePath: str = Field(default="", description="JD文件路径(可选)。如果有上传JD文件，则存储文件路径")

    status: int = Field(default=-1, description="分析状态（0：待分析，1：分析中，2：分析完成，3：分析失败）")

    analysisResult: str = Field(default="", description="分析结果（JSON格式）")

    retrievedResumes: list = Field(default=[], description="检索到的相似简历信息列表"),

    retrievedJds: list = Field(default=[], description="检索到的相似JD信息列表"),

    createTime: str = Field(default="", description="创建时间")
