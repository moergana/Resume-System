default_summary_criteria = "请根据input提供的内容，判断actual_output是否是对input的准确、全面且精炼的总结。"
default_summary_evaluation_steps = [
    "准确性：actual_output是否准确反映了input中的关键信息？",
    "全面性：actual_output是否涵盖了input中的主要内容和重要细节？",
    "精炼性：actual_output是否用简洁的语言表达了input的核心内容，避免冗余信息？",
    "忠实性：actual_output是否忠实于input的内容，有没有添加与input不符的信息或者自己编造信息？",
    "格式问题：不要关注input和actual_output的格式差异，只需要专注于二者的核心内容。对于JSON格式，需要将字段名和字段值的含义结合起来理解，而不是仅仅关注字段值内容的匹配程度。"
    "如果actual_output中出现了模糊的表达、不合逻辑或者自相矛盾的表达，请记住一切以input的内容为准，不要因此轻易降低对actual_output的评分。"
    "只要actual_output整体上能够准确、全面、精炼且忠实地总结input的内容，就可以给予高评分。"
]


resume_summary_criteria = '''
请根据input提供的内容，判断actual_output是否是对input的准确、全面且精炼的总结。
并且注意：
actual_output是结构化输出，它的内容和解释如下：
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

你只需要判断actual_output中的各个属性的内容是否准确、全面且精炼地总结了input的内容，不要关注除以上属性之外的内容是否被总结到！
'''
resume_summary_evaluation_steps = [
    "从准确性、全面性、精炼性和忠实性四个维度对结构化的actual_output中的各个属性进行评估，忽略除actual_output中的属性之外的内容。",
    "准确性：actual_output中的各个属性的内容是否准确反映了input中的关键信息？",
    "全面性：actual_output中的各个属性的内容是否涵盖了input中的主要内容和重要细节？",
    "精炼性：actual_output中的各个属性的内容是否用简洁的语言表达了input的核心内容，避免冗余信息？",
    "忠实性：actual_output中的各个属性的内容是否忠实于input的内容，有没有添加与input不符的信息或者自己编造信息？",
    "格式问题：不要关注input和actual_output的格式差异，只需要专注于二者的核心内容。对于JSON格式，需要将字段名和字段值的含义结合起来理解，而不是仅仅关注字段值内容的匹配程度。"
    "如果actual_output中出现了模糊的表达、不合逻辑或者自相矛盾的表达，请记住一切以input的内容为准，不要因此轻易降低对actual_output的评分。"
    "只要actual_output整体上能够准确、全面、精炼且忠实地总结input的内容，就可以给予高评分。"
]


jd_summary_criteria = '''
请根据input提供的内容，判断actual_output是否是对input的准确、全面且精炼的总结。
并且注意：
actual_output是结构化输出，它的内容和解释如下：
    title: str = Field(default="", description="职位名称。")
    company: str = Field(default="", description="招聘公司名称。")
    location: str = Field(default="", description="工作地点。")
    responsibilities: List[str] = Field(default=[], description="职位职责列表。")
    requirements: List[str] = Field(default=[], description="职位要求列表。")
    benefits: List[str] = Field(default=[], description="职位福利列表。")
    summary: str = Field(default="", description="对职位描述的综合总结。")

你只需要判断actual_output中的各个属性的内容是否准确、全面且精炼地总结了input的内容，不要关注除以上属性之外的内容是否被总结到！
'''
jd_summary_evaluation_steps = [
    "从准确性、全面性、精炼性和忠实性四个维度对结构化的actual_output中的各个属性进行评估，忽略除actual_output中的属性之外的内容。",
    "准确性：actual_output中的各个属性的内容是否准确反映了input中的关键信息？",
    "全面性：actual_output中的各个属性的内容是否涵盖了input中的主要内容和重要细节？",
    "精炼性：actual_output中的各个属性的内容是否用简洁的语言表达了input的核心内容，避免冗余信息？",
    "忠实性：actual_output中的各个属性的内容是否忠实于input的内容，有没有添加与input不符的信息或者自己编造信息？",
    "格式问题：不要关注input和actual_output的格式差异，只需要专注于二者的核心内容。对于JSON格式，需要将字段名和字段值的含义结合起来理解，而不是仅仅关注字段值内容的匹配程度。"
    "如果actual_output中出现了模糊的表达、不合逻辑或者自相矛盾的表达，请记住一切以input的内容为准，不要因此轻易降低对actual_output的评分。"
    "只要actual_output整体上能够准确、全面、精炼且忠实地总结input的内容，就可以给予高评分。"
]




advice_criteria = '''请根据input提供的简历和职位描述内容，判断actual_output是否是对input的合理评估和有效的建议。
并且注意：
actual_output是结构化输出，它的内容和解释如下：
    匹配度分数: int = Field(..., description="简历与职位描述的匹配度分数，百分制，范围0~100，分数越高表示匹配度越高。")
    简历改进建议: str = Field(..., description="""结合简历与职位描述的信息，针对当前简历的改进建议。
你可以选择以清单形式列出回答，同时注意在必要的地方换行，提升用户的阅读体验。
另外，你可以适当使用基础的markdown语法来增强可读性，例如使用粗体、斜体等格式。""")
    求职建议: str = Field(..., description="""结合简历与职位描述的信息，针对后续求职的建议。
你可以选择以清单形式列出回答，同时注意在必要的地方换行，提升用户的阅读体验。
另外，你可以适当使用基础的markdown语法来增强可读性，例如使用粗体、斜体等格式。""")

你只需要判断actual_output中的匹配度分数是否合理地反映了input中简历内容与职位描述内容的匹配程度，以及actual_output中的建议内容是否合理、相关且具有实用性，不要关注除以上内容之外的内容是否被包含在建议中！
'''
advice_evaluation_steps = [
    "匹配度分数的合理性：actual_output中的匹配度分数是否合理地反映了input中简历内容与职位描述内容的匹配程度？",
    "建议的相关性：actual_output中的建议内容是否与input中的简历内容和职位描述内容相关联？",
    "建议的实用性：actual_output中的建议内容是否具有实际可操作性，能够帮助求职者改进简历或者提升求职能力？",
    "建议的针对性：actual_output中的建议内容是否针对input中的具体情况提出，而不是泛泛而谈的通用建议？",
    "建议的表达清晰度：actual_output中的建议内容是否表达清晰、易于理解，避免模糊不清或者晦涩难懂的表述？",
    "如果actual_output中出现了模糊的表达、不合逻辑或者自相矛盾的表达，请记住一切以input的内容为准，不要因此轻易降低对actual_output的评分。"
    "只要actual_output整体上能够针对input中简历和职位描述的给出合理的评估和准确且实用的建议，就可以给予高评分。"
]




difference_criteria = '''请根据input提供的简历和职位描述内容，判断actual_output是否是对input的合理评估和有效的分析。
并且注意：
actual_output是结构化输出，它的内容和解释如下：
    匹配度分数: int = Field(..., description="简历与职位描述的匹配度分数，百分制，范围0~100，分数越高表示匹配度越高。")
    差异点分析: str = Field(..., description="""简历与职位描述之间的具体差异点，比如某项技能的缺失，某个项目与职位不匹配等。
你可以选择以清单形式列出回答，同时注意在必要的地方换行，提升用户的阅读体验。
另外，你可以适当使用基础的markdown语法来增强可读性，例如使用粗体、斜体等格式。""")

你只需要判断actual_output中的匹配度分数是否合理地反映了input中简历内容与职位描述内容的匹配程度，以及actual_output中的差异点分析内容是否相关且分析合理，不要关注除以上内容之外的内容是否被包含在分析中！
'''
difference_evaluation_steps = [
    "匹配度分数的合理性：actual_output中的匹配度分数是否合理地反映了input中简历内容与职位描述内容的匹配程度？",
    "差异点分析的相关性：actual_output中的差异点分析内容是否与input中的简历内容和职位描述内容相关联？",
    "差异点分析的针对性：actual_output中的差异点分析内容是否针对input中的具体情况提出，而不是泛泛而谈的通用分析？",
    "差异点分析的合理性：actual_output中的差异点分析内容是否合理，能够准确指出input中简历和职位描述之间的具体差异点，并且分析这些差异点的原因或者影响？",
    "差异点分析的表达清晰度：actual_output中的差异点分析内容是否表达清晰、易于理解，避免模糊不清或者晦涩难懂的表述？",
    "如果actual_output中出现了模糊的表达、不合逻辑或者自相矛盾的表达，请记住一切以input的内容为准，不要因此轻易降低对actual_output的评分。"
    "只要actual_output整体上能够针对input中简历和职位描述的给出合理的评估和准确的差异点分析，就可以给予高评分。"
]



default_retrieve_resume_criteria = '''请根据input提供的职位描述内容，判断actual_output中检索到的简历内容是否与input中的职位描述内容相关。
并且注意：
actual_output是结构化输出，它的内容和解释如下：
    Rank i: int = Field(..., description="检索结果中排名，i值越小表示排名越靠前，在检索结果中表示相关性越高")
    Resume Content: str = Field(..., description="检索结果中对应Rank的简历内容字符串。")
    
你需要判断actual_output中检索到的简历内容是否与input中的职位描述内容相关，并且相关性的排名是否合理（排名靠前的是否比排名靠后的相关性更高）。
'''
default_retrieve_resume_evaluation_steps = [
    "内容相关性：actual_output中的简历内容是否与input中的职位描述内容相关联？actual_output中的简历是否与input中的职位描述中提到的关键技能、经验或者其他要求有关？",
    "排名合理性：actual_output中检索到的简历内容的相关性排名是否合理？排名靠前的简历内容是否比排名靠后的简历内容更符合input中的职位描述的要求？",
    "只要actual_output的内容与input的内容的相关性高，并且排名依据相关性来看是合理的，就可以给予高评分。"
]



default_retrieve_jd_criteria = '''请根据input提供的简历内容，判断actual_output中检索到的职位描述内容是否与input中的简历内容相关。
并且注意：
actual_output是结构化输出，它的内容和解释如下：
    Rank i: int = Field(..., description="检索结果中排名，i值越小表示排名越靠前，在检索结果中表示相关性越高")
    JD Content: str = Field(..., description="检索结果中对应Rank的职位描述内容字符串。")
    
你需要判断actual_output中检索到的职位描述内容是否与input中的简历内容相关，并且相关性的排名是否合理（排名靠前的是否比排名靠后的相关性更高）。
'''
default_retrieve_jd_evaluation_steps = [
    "内容相关性：actual_output中的职位描述内容是否与input中的简历内容相关联？input中的简历是否与actual_output中职位描述中提到的关键技能、经验或者其他要求有关？",
    "排名合理性：actual_output中检索到的职位描述内容的相关性排名是否合理？排名靠前的职位描述内容是否比排名靠后的职位描述内容更适配input中的简历内容？",
    "只要actual_output的内容与input的内容的相关性高，并且排名依据相关性来看是合理的，就可以给予高评分。"
]