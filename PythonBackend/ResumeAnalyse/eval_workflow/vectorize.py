from curses import meta
import os
from typing import List

from langchain_milvus import BM25BuiltInFunction, Milvus
import numpy as np
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

from rdflib import collection
from unstructured import documents

from ResumeAnalyse.entity.summary import JDSummary, ResumeSummary
from ResumeAnalyse.constants import MMR_FUNCTION, RRF_K, SIMILARITY_FUNCTION, SIMILARITY_BM25_FUNCTION
from ResumeAnalyse.eval_workflow.commons import settings, workspace_root


"""
嵌入模型配置
"""
# example: embed_model_name = "Qwen/Qwen3-Embedding-0.6B"
embed_model_name = settings["Model"]["Embed_Model_Name"]
embed_model = HuggingFaceEmbeddings(model_name=embed_model_name)

resume_collection_name = "resume_collection"
# resume_collection_persist_directory = workspace_root + "/chroma_data/resumes"
resume_collection_persist_directory = os.path.join(workspace_root, "chroma_data", "resumes")

JD_collection_name = "JD_collection"
# JD_collection_persist_directory = workspace_root + "/chroma_data/JDs"
JD_collection_persist_directory = os.path.join(workspace_root, "chroma_data", "JDs")
""" 
# 初始化Chroma向量数据库实例
resume_vectordb = Chroma(
    collection_name=resume_collection_name,
    embedding_function=embed_model,
    persist_directory=resume_collection_persist_directory,
)

JD_vectordb = Chroma(
    collection_name=JD_collection_name,
    embedding_function=embed_model,
    persist_directory=JD_collection_persist_directory,
)
"""

# 初始化Milvus向量数据库实例
# Milvus相比于Chroma，具有更高的性能和可扩展性，适合处理大规模的向量数据和高并发的查询请求。
# 首先，定义Milvus向量数据库的collection在本地保存的文件路径（这和Chroma使用一个目录是不同的）
milvus_collection_dir = os.path.join(workspace_root, "milvus_data")
if not os.path.exists(milvus_collection_dir):
    os.makedirs(milvus_collection_dir)
    logging.info(f"Created directory for Milvus collections at {milvus_collection_dir}.")
resume_collection_db_file = os.path.join(workspace_root, "milvus_data", "resumes_collection.db")
JD_collection_db_file = os.path.join(workspace_root, "milvus_data", "JDs_collection.db")

# 定义Milvus向量数据库实例，指定embedding_function、collection_name和connection_args等参数
resume_vectordb = Milvus(
    embedding_function=embed_model,
    collection_name=resume_collection_name,  # 指定 collection 名称
    connection_args={
        "uri": resume_collection_db_file,  # collection保存的文件路径
    },
    # 混合检索必需的配置
    builtin_function=BM25BuiltInFunction(),
    vector_field=["dense", "sparse"],
    index_params=[
        {"metric_type": "COSINE", "index_type": "FLAT"},
        {"metric_type": "BM25", "index_type": "SPARSE_INVERTED_INDEX", "params": {"drop_ratio_build": 0.2}}
    ],
    auto_id=False,   # 禁用自动生成ID，需要在添加文档时手动指定ID，且ID必须是字符串类型。
    drop_old=False,  # 如果已存在同名 collection 则删除重建。如果是生产环境想复用，设为 False
)

JD_vectordb = Milvus(
    embedding_function=embed_model,
    collection_name=JD_collection_name,  # 指定 collection 名称
    connection_args={
        "uri": JD_collection_db_file,  # collection保存的文件路径
    },
    # 混合检索必需的配置
    builtin_function=BM25BuiltInFunction(),
    vector_field=["dense", "sparse"],
    index_params=[
        {"metric_type": "COSINE", "index_type": "FLAT"},
        {"metric_type": "BM25", "index_type": "SPARSE_INVERTED_INDEX", "params": {"drop_ratio_build": 0.2}}
    ],
    auto_id=False,   # 禁用自动生成ID，需要在添加文档时手动指定ID，且ID必须是字符串类型。
    drop_old=False,  # 如果已存在同名 collection 则删除重建。如果是生产环境想复用，设为 False
)



def handle_dict(data: dict) -> str:
    """将字典数据格式化为字符串表示。

    Args:
        data (dict): 需要格式化的字典数据。

    Returns:
        str: 格式化后的字符串表示。
        输出示例：
        key1: value1; key2: value2; ...
    """
    items = []
    for key, value in data.items():
        items.append(f"{key}: {value}")
    return "; ".join(items)


def handle_resumes_contents(resume_contents: List[ResumeSummary]) -> List[str]:
    """处理ResumeSummary对象列表，提取并格式化简历文本内容。

    Args:
        resume_contents (List[ResumeSummary]): ResumeSummary对象列表。

    Returns:
        List[str]: 格式化后的简历文本内容列表。
    """
    formatted_resumes = []
    for resume in resume_contents:
        resume_text = f"""姓名: {resume.name}
年龄: {resume.age}
教育背景: {handle_dict(resume.education)}
工作经验: {'; '.join(resume.experience)}
项目经历: {'; '.join(resume.projects)}
专业技能: {'; '.join(resume.skills)}
求职目标: {resume.target}
相关证书: {'; '.join(resume.certifications)}
综合素质总结: {resume.summary}
"""
        formatted_resumes.append(resume_text)
    return formatted_resumes


def handle_JD_contents(JD_contents: List[JDSummary]) -> List[str]:
    """处理职位描述（JD）文本内容，进行必要的格式化。

    Args:
        JD_contents (List[JDSummary]): 原始JD文本内容列表。

    Returns:
        List[str]: 格式化后的JD文本内容列表。
    """
    # 目前假设JD文本已经是纯文本格式，无需额外处理
    formatted_JDs = []
    for jd in JD_contents:
        jd_text = f"""职位名称: {jd.title}
公司名称: {jd.company}
工作地点: {jd.location}
职位职责: {'; '.join(jd.responsibilities)}
职位要求: {'; '.join(jd.requirements)}
职位福利: {'; '.join(jd.benefits)}
职位描述总结: {jd.summary}
"""
        formatted_JDs.append(jd_text)
    return formatted_JDs


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """
    计算余弦相似度similarity
    """
    nd_a, nd_b = np.array(a), np.array(b)
    denom = (np.linalg.norm(nd_a) * np.linalg.norm(nd_b))
    sim = float(nd_a @ nd_b / denom) if denom else 0.0
    # 将原本的[-1,1]范围归一化到[0,1]范围
    sim = (sim + 1) / 2
    return sim


def add_resumes_to_vector_db(resume_texts: List[str], ids: list[str]) -> None:
    """将简历文本添加到向量数据库中。

    Args:
        resume_texts ( List[str]): 简历文本内容列表。
        ids (list[str]): 对应的简历ID列表。
    """
    logging.info(f"Starting to add {len(resume_texts)} resumes to the vector database as follow: {ids}")
    """
    # 使用递归字符文本分割器对简历进行分块
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=200,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"],
    )
    # 遍历所有的简历文本内容，分割并添加到向量数据库
    for index, resume_text in enumerate(resume_contents):
        split_str = splitter.split_text(resume_text)
        metadata = {
            "resume_id": ids[index],
        }
        resume_vectordb.add_texts(texts=split_str,
                                  metadatas=[metadata for _ in range(len(split_str))],
                                  ids=[f"{ids[index]}_part{j}" for j in range(len(split_str))])
        logging.info(f"Added resume ID {ids[index]} with {len(split_str)} chunks to the vector database.")\
    """
    # 由于简历内容已经经过LLM精炼，不进行分块，直接添加到向量数据库
    # 为了提高添加效率，批量添加简历文本内容到向量数据库中，同时为每个简历文本指定对应的ID和metadata
    metadatas = []
    for index, resume_text in enumerate(resume_texts):
        metadata = {
            "resume_id": ids[index],
        }
        metadatas.append(metadata)
        
    resume_vectordb.add_texts(texts=resume_texts,
                              metadatas=metadatas,
                              ids=ids)
    logging.info(f"Added resumes (IDs: {ids}) to the vector database.")

    logging.info(f"All {len(resume_texts)} resumes have been added to the vector database successfully.")


def retrieve_resumes(JD: str,
                     search_type: str = None,
                     k: int = 3,
                     fetch_k: int = 20,
                     lambda_mult: float = 0.5) -> List[dict]:
    """根据查询（比如职位描述JD）从向量数据库中检索相关简历片段。

    Args:
        JD (str): 查询用的JD。
        search_type (str, optional): 检索方法，支持"similarity"、"mmr"和"similarity_bm25". 
                                    如果是Milvus数据库，则默认为"similarity_bm25"，为similarity和BM25的混合检索. 否则默认为"similarity".
        k (int, optional): 检索的简历数量. Defaults to 3.
        fetch_k (int, optional): MMR检索时的预检索数量. Defaults to 20.
        lambda_mult (float, optional): MMR检索时的多样性调节参数. Defaults to 0.5.
    Returns:
        list[dict]: 检索到的简历列表，每个简历以字典形式返回。
        字典结构：
        {
            "resume_id": str,  # 简历ID
            "content": str,   # 简历文本内容
            "similarity_score": float,  # 与JD的相似度得分
            "rank": int  # 排名
        }
    """
    # 如果search_type参数没有指定，根据向量数据库的类型设置默认的检索方法
    if isinstance(resume_vectordb, Milvus) and search_type == None:
        search_type = SIMILARITY_BM25_FUNCTION
    else:
        search_type = SIMILARITY_FUNCTION
    
    # 检索相关的简历，同时返回相似度
    # 基于Embedding向量的内积的相似度检索，同时返回相似度得分
    if search_type == SIMILARITY_FUNCTION:
        logging.info(f"Retrieving top {k} resumes for the JD using similarity search.")
        retrieve_results = resume_vectordb.similarity_search_with_score(
            query=JD, 
            k=k
        )
        # 处理检索得到的List[Tuple[Document, float]]对象，提取文本内容和相似度
        results = []
        for i, (doc, score) in enumerate(retrieve_results):
            metadata = doc.metadata
            content = doc.page_content
            results.append({
                "resume_id": metadata.get("resume_id", f"unknown_id_{i}"),
                "content": content,
                "similarity_score": score
            })
            
    # 基于MMR（最大边际相关性）的检索，能够在保证相关性的同时增加结果的多样性，适合需要多样化结果的场景
    elif search_type == MMR_FUNCTION:
        logging.info(f"Retrieving top {k} resumes for the JD using MMR search.")
        retrieve_results = resume_vectordb.max_marginal_relevance_search(
            query=JD,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult
        )
        # 处理检索得到的List[Document]对象，提取文本内容并另外计算相似度similarity
        query_emb = embed_model.embed_query(JD)
        results = []
        for i, doc in enumerate(retrieve_results):
            metadata = doc.metadata
            content = doc.page_content
            doc_content_emb = embed_model.embed_query(content)
            sim = _cosine_sim(query_emb, doc_content_emb)  #
            results.append({
                "resume_id": metadata.get("resume_id", f"unknown_id_{i}"),
                "content": content,
                "similarity_score": sim
            })
            
    # 基于相似度和BM25的混合检索，能够结合两者的优势，在保证相关性的同时兼顾文本匹配的精确性，适合需要兼顾语义理解和关键词匹配的场景
    # 该混合检索策略为默认使用的检索策略，能够在大多数场景下提供较好的检索效果
    elif search_type == SIMILARITY_BM25_FUNCTION:
        # 该混合检索算法是Milvus特有的实现，在其他向量数据库中（比如Chroma）可能没有同样的实现，使用时需要确保向量数据库支持该算法
        if not isinstance(resume_vectordb, Milvus):
            raise ValueError(f"similarity_bm25 search_type requires the vector database to be Milvus, but got {type(resume_vectordb)}")
        logging.info(f"Retrieving top {k} resumes for the JD using hybrid search: similarity + BM25.")
        retrieve_results = resume_vectordb.similarity_search_with_score(
            query=JD, 
            k=k,
            ranker_type="rrf", 
            ranker_params={"k": RRF_K}
        )
        # 处理检索得到的List[Tuple[Document, float]]对象，提取文本内容和相似度
        results = []
        for i, (doc, score) in enumerate(retrieve_results):
            metadata = doc.metadata
            content = doc.page_content
            results.append({
                "resume_id": metadata.get("resume_id", f"unknown_id_{i}"),
                "content": content,
                "similarity_score": score
            })
    else:
        raise ValueError(f"Unsupported search_type: {search_type}")
    # 将results按照相似度得分从高到低排序
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    for i in range(len(results)):
        results[i].update({"rank": i + 1})

    logging.info("Formatted retrieved resumes successfully.")
    logging.debug(f"Formatted retrieved resumes: \n{results}")
    return results


def add_JDs_to_vector_db(JD_texts: List[str], ids: list[str]) -> None:
    """
    将职位描述（JD）文本添加到向量数据库中。
    :param JD_contents:
    :param ids:
    :return:
    """
    logging.info(f"Starting to add {len(JD_texts)} JDs to the vector database as follow: {ids}")
    # 遍历所有的JD文本内容，分割并添加到向量数据库
    """
    for index, jd_text in enumerate(JD_texts):
        metadata = {
            "JD_id": ids[index],
        }
        JD_vectordb.add_texts(texts=split_str,
                              metadatas=[metadata for _ in range(len(split_str))],
                              ids=[f"{ids[index]}_part{j}" for j in range(len(split_str))])
        logging.info(f"Added JD ID {ids[index]} with {len(split_str)} chunks to the vector database.")

    logging.info(f"All {len(JD_texts)} JDs have been added to the vector database successfully.")
    """
    # 由于JD内容已经经过LLM精炼，不进行分块，直接添加到向量数据库
    # 为了提高添加效率，批量添加JD文本内容到向量数据库中，同时为每个JD文本指定对应的ID和metadata
    metadatas = []
    for index, jd_text in enumerate(JD_texts):
        metadata = {
            "JD_id": ids[index],
        }
        metadatas.append(metadata)

    JD_vectordb.add_texts(texts=JD_texts,
                            metadatas=metadatas,
                            ids=ids)
    logging.info(f"Added JDs (IDs: {ids}) to the vector database.")

    logging.info(f"All {len(JD_texts)} JDs have been added to the vector database successfully.")


def retrieve_JDs(resume: str,
                 search_type: str = None,
                 k: int = 3,
                 fetch_k: int = 20,
                 lambda_mult: float = 0.5) -> List[dict]:
    """根据提供的简历内容，从向量数据库中检索相关的JD（职位描述）。

    Args:
        resume (str): 查询用的简历内容。
        search_type (str, optional): 检索方法，支持"similarity"、"mmr"和"similarity_bm25". 
                                    如果是Milvus数据库，则默认为"similarity_bm25"，为similarity和BM25的混合检索. 否则默认为"similarity".
        k (int, optional): 检索的简历数量. Defaults to 3.
        fetch_k (int, optional): MMR检索时的预检索数量. Defaults to 20.
        lambda_mult (float, optional): MMR检索时的多样性调节
    Returns:
        list[dict]: 检索到的简历列表，每个简历以字典形式返回。
        字典结构：
        {
            "JD_id": str,  # JD ID
            "content": str,   # JD文本内容
            "similarity_score": float,  # 与简历的相似度得分
            "rank": int  # 排名
        }
    """
    # 如果search_type参数没有指定，根据向量数据库的类型设置默认的检索方法
    if isinstance(JD_vectordb, Milvus) and search_type == None:
        search_type = SIMILARITY_BM25_FUNCTION
    else:
        search_type = SIMILARITY_FUNCTION
    
    # 检索相关的JD，同时返回相似度
    # 基于Embedding向量的内积的相似度检索，同时返回相似度得分
    if search_type == SIMILARITY_FUNCTION:
        logging.info(f"Retrieving top {k} JDs for the resume using similarity search.")
        # similarity_search_with_relevance_scores和similarity_search_with_score是不一样的
        # 前者的分数是相似度分数，范围[0,1]，越大表示越相似；后者的分数是距离分数，范围[0,+inf)，越小表示越相似
        retrieve_results = JD_vectordb.similarity_search_with_relevance_scores(
            query=resume, 
            k=k
        )
        # 处理检索得到的List[Tuple[Document, float]]对象，提取文本内容和相似度
        results = []
        for i, (doc, score) in enumerate(retrieve_results):
            metadata = doc.metadata
            content = doc.page_content
            results.append({
                "JD_id": metadata.get("JD_id", f"unknown_id_{i}"),
                "content": content,
                "similarity_score": score
            })
    # 基于MMR（最大边际相关性）的检索，能够在保证相关性的同时增加结果的多样性，适合需要多样化结果的场景
    elif search_type == MMR_FUNCTION:
        logging.info(f"Retrieving top {k} JDs for the resume using MMR search.")
        retrieve_results = JD_vectordb.max_marginal_relevance_search(
            query=resume,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult
        )
        # 处理检索得到的List[Document]对象，提取文本内容并另外计算相似度similarity
        query_emb = embed_model.embed_query(resume)
        results = []
        for i, doc in enumerate(retrieve_results):
            metadata = doc.metadata
            content = doc.page_content
            doc_content_emb = embed_model.embed_query(content)
            sim = _cosine_sim(query_emb, doc_content_emb)  #
            results.append({
                "JD_id": metadata.get("JD_id", f"unknown_id_{i}"),
                "content": content,
                "similarity_score": sim
            })
    # 基于相似度和BM25的混合检索，能够结合两者的优势，在保证相关性的同时兼顾文本匹配的精确性，适合需要兼顾语义理解和关键词匹配的场景
    # 该混合检索策略为默认使用的检索策略，能够在大多数场景下提供较好的检索效果
    elif search_type == SIMILARITY_BM25_FUNCTION:
        # 该混合检索算法是Milvus特有的实现，在其他向量数据库中（比如Chroma）可能没有同样的实现，使用时需要确保向量数据库支持该算法
        if not isinstance(JD_vectordb, Milvus):
            raise ValueError(f"similarity_bm25 search_type requires the vector database to be Milvus, but got {type(JD_vectordb)}")
        logging.info(f"Retrieving top {k} JDs for the resume using hybrid search: similarity + BM25.")
        retrieve_results = JD_vectordb.similarity_search_with_score(
            query=resume, 
            k=k,
            ranker_type="rrf", 
            ranker_params={"k": RRF_K}
        )
        # 处理检索得到的List[Tuple[Document, float]]对象，提取文本内容和相似度
        results = []
        for i, (doc, score) in enumerate(retrieve_results):
            metadata = doc.metadata
            content = doc.page_content
            results.append({
                "JD_id": metadata.get("JD_id", f"unknown_id_{i}"),
                "content": content,
                "similarity_score": score
            })
    else:
        raise ValueError(f"Unsupported search_type: {search_type}")

    # 将results按照相似度得分从高到低排序
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    for i in range(len(results)):
        results[i].update({"rank": i + 1})

    logging.info("Formatted retrieved resumes successfully.")
    logging.debug(f"Formatted retrieved resumes: \n{results}")
    return results


if __name__ == "__main__":
    # Mock简历数据
    resumeSummary = ResumeSummary()
    resumeSummary.name = "项炎"
    resumeSummary.age = 37
    resumeSummary.education = {"学校": "北京科技经营管理学院", "学位": "学士学位", "毕业年份": "2010.06"}
    resumeSummary.experience = [
        "2007.03-2010.07：广州云蝶科技有限公司，产品开发，负责Unity场景搭建、灯光渲染、性能优化等工作。",
        "2005.04-2018.04：前程无忧（长沙），试剂生产员（生物），负责行政支持、物资管理、档案整理等工作。",
        "1990.06-2016.12：T3出行，诉讼部诉讼秘书，负责运营文件起草、制度监控、销售报表分析等工作。",
        "2007.06-2017.02：嘉展国际，财务业务员，负责医药产品招商推广、市场规划、代理商管理等工作。"]
    resumeSummary.projects = [
        "2000.04-2011.04：信息化条件下宣传思想工作研究，负责多媒体运营渠道拓展、广告资源整合等工作。",
        "2006.05-2013.12：自媒体时代主流意识形态话语面临的挑战及对策研究，协调拍摄资源、解决拍摄问题等工作。",
        "2006.01-2010.10：岭南文化融入大学生思想政治教育研究，负责台账管理、客户资料归档、人事工作等。"]
    resumeSummary.skills = ["Unity场景搭建与渲染", "游戏性能优化", "行政管理与协调", "市场推广与销售",
                            "多媒体运营与广告投放",
                            "项目协调与资源管理"]
    resumeSummary.target = "前端开发"
    resumeSummary.certifications = ["未提供"]
    resumeSummary.summary = "项炎拥有3年工作经验，学士学位，擅长Unity开发、行政管理、市场推广等多领域工作。在前端开发领域有明确的职业目标，具备较强的项目协调和资源管理能力。"

    # Mock职位描述数据
    JD_summary = JDSummary()
    JD_summary.title = "前端开发工程师"
    JD_summary.company = "Tech Innovators Ltd."
    JD_summary.location = "北京"
    JD_summary.responsibilities = ["负责公司网站和应用的前端开发与维护",
                                   "与设计团队合作，实现高质量的用户界面",
                                   "优化网站性能，提升用户体验",
                                   "参与需求分析和技术方案制定"]
    JD_summary.requirements = ["熟悉JavaScript、HTML、CSS等前端技术",
                               "有React或Vue.js等主流框架的开发经验",
                               "具备良好的代码编写习惯和团队合作精神",
                               "有相关项目经验者优先考虑"]
    JD_summary.benefits = ["具有竞争力的薪资待遇",
                           "弹性工作时间和远程办公选项",
                           "完善的培训和职业发展机会",
                           "丰富的员工活动和团队建设活动"]
    JD_summary.summary = """Tech Innovators Ltd.正在北京招聘一位经验丰富的前端开发工程师，负责网站和应用的前端开发与维护，
    要求熟悉JavaScript、HTML、CSS等前端技术，并有React或Vue.js等框架的开发经验。
    公司提供具有竞争力的薪资待遇、弹性工作时间、远程办公选项以及完善的培训和职业发展机会。"""

    # 测试将简历摘要添加到向量数据库
    # add_resumes_to_vector_db([resumeSummary], ["resume_test_1"])

    # 测试从向量数据库中检索简历
    JD_markdown_res = """
                        招聘前端开发工程师
                        ## 工作地点：北京
                        ## 公司名称：Tech Innovators Ltd.
                        ## 职位描述：
                        我们正在寻找一位经验丰富的前端开发工程师加入我们的团队。
                        主要职责包括：
                        - 负责公司网站和应用的前端开发与维护
                        - 与设计团队合作，实现高质量的用户界面
                        - 优化网站性能，提升用户体验
                        - 参与需求分析和技术方案制定
                        ## 职位要求：
                        - 熟悉JavaScript、HTML、CSS等前端技术
                        - 有React或Vue.js等主流框架的开发经验
                        - 具备良好的代码编写习惯和团队合作精神
                        - 有相关项目经验者优先考虑
                        ## 福利待遇：
                        - 具有竞争力的薪资待遇
                        - 弹性工作时间和远程办公选项
                        - 完善的培训和职业发展机会
                        - 丰富的员工活动和团队建设活动
                        """
    search_results = retrieve_resumes(JD_markdown_res)

    print("Search Results:\n", search_results)
