import asyncio
import json
import logging
import contextlib
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
import uvicorn

# 导入 Conversation.py 及其他模块中的必要组件
from ResumeAnalyse.Conversation import (
    init_graph_executor,
    sessions_context_register,
    init_conversation_agent,
    invoke_conversation_graph_in_background,
    _message_to_text,
)
import ResumeAnalyse.Conversation as Conv
from ResumeAnalyse.constants import (
    get_resume_analysis_redis_key,
    RESUME_ANALYSIS_CUCKOO_FILTER_REDIS_KEY,
    RESUME_ANALYSIS_REDIS_TTL,
    NULL_REDIS_TTL
)
from ResumeAnalyse.utils import redis_client, mysql_engine
from langchain_core.messages import AIMessage


app = FastAPI(title="Conversation Agent API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:8080"],  # 只接受来自网关的请求
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",     # 允许来自 localhost 和 127.0.0.1 的所有端口的请求
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有类型的请求，包括 OPTIONS
    allow_headers=["*"],
)


# 定义chat接口的请求数据模型
class ChatRequest(BaseModel):
    session_id: str     # 会话ID
    analysis_id: Optional[str] = ""     # 分析记录ID，关联到特定的简历分析任务，如果没有提供则进入无背景数据的临时会话模式
    message: str    # 用户发送的消息内容


async def chat_stream_generator(request_data: ChatRequest):
    task = None
    try:
        # 确保初始化了 conversation_graph_executor_with_checkpointer
        if Conv.conversation_graph_executor_with_checkpointer is None:
            await init_graph_executor()
        
        session_id = request_data.session_id
        analysis_id = request_data.analysis_id
        message = request_data.message

        logging.info(f"收到来自 session_id: {session_id} 的 API 请求, analysis_id: {analysis_id}")
        
        graph_need_memory = True
        if analysis_id == "":
            logging.info(f"Session {session_id} 未提供 analysis_id 参数，进入无预生成数据的临时会话模式。")
            graph_need_memory = False
            # 为没有提供 analysis_id 的会话创建一个临时的 analysis_id，格式为 "temp-{session_id}"
            # 这是为了避免临时会话的Agent资源不缓存而导致后续同一会话的每次请求都要重新创建Agent的问题
            analysis_id = f"temp-{session_id}"
            logging.info(f"为 session_id: {session_id} 创建临时会话，该临时会话的analysis_id: {analysis_id}")

        # 判断对话智能体是否已经被初始化。如果没有就调用init_conversation_agent
        if analysis_id not in sessions_context_register:
            logging.info("对话智能体尚未初始化! 尝试初始化对话智能体中...")

            # --- 数据获取逻辑 ---
            # 首先查询 Redis 中的 Cuckoo Filter，如果过滤器中不存在该 analysis_id，则说明没有对应的预生成数据
            hasFilter = True if redis_client.exists(RESUME_ANALYSIS_CUCKOO_FILTER_REDIS_KEY) == 1 else False
            if hasFilter and (not redis_client.cf().exists(RESUME_ANALYSIS_CUCKOO_FILTER_REDIS_KEY, str(analysis_id))):
                logging.info(f"Redis Cuckoo Filter中不存在 analysis_id: {analysis_id}，将不使用预生成数据初始化智能体。")
                resume_summary_text = ""
                jd_summary_text = ""
                differences = ""
                match_score = -1
                improvement_suggestions = ""
                job_hunting_advice = ""
            else:
                if not hasFilter:
                    logging.error(f"Redis中不存在 Cuckoo Filter，Key: {RESUME_ANALYSIS_CUCKOO_FILTER_REDIS_KEY}。"
                                  f"跳过过滤器检查，开始尝试从Redis中获取预生成数据初始化智能体。")
                else:
                    logging.info(f"Redis Cuckoo Filter中存在 analysis_id: {analysis_id}，尝试使用预生成数据初始化智能体。")
                    
                # 从 Redis 中获取预生成的数据
                redis_key = get_resume_analysis_redis_key(analysis_id)
                init_data = redis_client.hgetall(redis_key)
                
                if init_data and init_data != {}:
                    resume_summary_text = init_data.get("resume_summary_text", "")
                    jd_summary_text = init_data.get("jd_summary_text", "")
                    differences = init_data.get("differences", "")
                    match_score = init_data.get("match_score", -1)
                    improvement_suggestions = init_data.get("improvement_suggestions", "")
                    job_hunting_advice = init_data.get("job_hunting_advice", "")
                    # 刷新过期时间
                    redis_client.expire(redis_key, RESUME_ANALYSIS_REDIS_TTL)
                else:
                    # Redis中没能找到预生成数据，尝试从MySQL中获取
                    is_exist = True
                    with mysql_engine.connect() as connection:
                        logging.info(f"Redis中未找到预生成数据，尝试从MySQL中获取。分析记录ID: {analysis_id}")
                        logging.info(f"正在查询表 tb_resume_analysis 中的预生成数据，分析记录ID: {analysis_id}")
                        result = connection.execute(
                            text("SELECT analysis_result FROM tb_resume_analysis WHERE id = :id"),
                            {"id": analysis_id}
                        )
                        row = result.fetchone()
                        if row:
                            # 从Row对象中获取analysis_result字段的值，并解析为JSON
                            analysis_result_json = json.loads(row.analysis_result)
                            match_score = analysis_result_json.get("match_score", -1)
                            differences = analysis_result_json.get("differences", "")
                            improvement_suggestions = analysis_result_json.get("improvement_suggestions", "")
                            job_hunting_advice = analysis_result_json.get("job_hunting_tips", "")
                        else:
                            logging.info(f"tb_resume_analysis表中未找到预生成数据，分析记录ID: {analysis_id}")
                            match_score = -1
                            differences = ""
                            improvement_suggestions = ""
                            job_hunting_advice = ""
                            is_exist = False

                        logging.info(f"正在查询表 tb_analysis_summary 中的预生成数据，分析记录ID: {analysis_id}")
                        result = connection.execute(
                            text("SELECT resume_summary_text, jd_summary_text FROM tb_analysis_summary WHERE analysis_id = :id"),
                            {"id": analysis_id}
                        )
                        row = result.fetchone()
                        if row:
                            logging.info(f"tb_analysis_summary中发现预生成数据，分析记录ID: {analysis_id}")
                            resume_summary_text = row.resume_summary_text or ""
                            jd_summary_text = row.jd_summary_text or ""
                        else:
                            logging.info(f"tb_analysis_summary中未找到预生成数据，记录分析ID: {analysis_id}")
                            resume_summary_text = ""
                            jd_summary_text = ""
                            is_exist = False
                        
                        # 如果从MySQL中成功获取到了预生成数据，则将其存入Redis，便于下次快速获取
                        if is_exist:
                            logging.info(f"从MySQL中成功获取到预生成数据，正在缓存到Redis中。Redis Key: {redis_key}")
                            # 将查询结果存入Redis，便于下次快速获取
                            redis_client.hset(redis_key, mapping={
                                "resume_summary_text": resume_summary_text,
                                "jd_summary_text": jd_summary_text,
                                "differences": differences,
                                "match_score": match_score,
                                "improvement_suggestions": improvement_suggestions,
                                "job_hunting_advice": job_hunting_advice,
                            })
                            redis_client.expire(redis_key, RESUME_ANALYSIS_REDIS_TTL)  # 设置过期时间
                            logging.info(f"预生成数据已成功缓存到Redis。Redis Key: {redis_key}")
                        else:
                            # 如果MySQL中没能够获取到预生成数据，则在Redis中插入一个空记录，避免缓存穿透
                            logging.info(f"未能从MySQL中获取到预生成数据。分析记录ID: {analysis_id}")
                            logging.info(f"将不使用预生成数据初始化智能体...")
                            redis_client.hset(redis_key, mapping={})
                            redis_client.expire(redis_key, NULL_REDIS_TTL)

            agent, config = await init_conversation_agent(
                analysis_id,
                resume_summary_text=resume_summary_text,
                jd_summary_text=jd_summary_text,
                match_score=match_score,
                differences=differences,
                improvement_suggestions=improvement_suggestions,
                job_hunting_advice=job_hunting_advice,
            )
            
            # 将 Agent 和 Config 存入全局字典，实现持久化。
            # 使用analysis_id作为键，确保每个分析记录的会话是独立的。
            sessions_context_register[analysis_id] = {
                "conversation_agent": agent,
                "conversation_config": config
            }
            logging.info("对话智能体初始化完成。")

        # 从全局字典中获取当前用户的 Agent 和 Config
        user_context = sessions_context_register[analysis_id]
        conversation_agent = user_context["conversation_agent"]
        config = user_context["conversation_config"]

        queue = asyncio.Queue()
        
        if graph_need_memory:
            logging.info(f"会话 {session_id} 需要记忆功能，将使用持久化的 Conversation Graph Executor With Checkpointer。")
            graph_executor = Conv.conversation_graph_executor_with_checkpointer
        else:
            logging.info(f"会话 {session_id} 不需要记忆功能，将使用不带持久化的 Conversation Graph Executor。")
            graph_executor = Conv.conversation_graph_executor

        # 启动后台任务，让模型根据用户的输入生成回复（不要await，应该用asyncio在事件循环中添加一个新的任务，且当前协程不等待它）
        task = asyncio.create_task(invoke_conversation_graph_in_background(queue, message, conversation_agent, graph_executor, config))

        while True:
            chunk = await queue.get()

            if chunk is None:
                break
            
            # 如果生成过程中出现了错误，chunk可能是一个包含错误信息的字典，此时需要将错误信息发送给前端，并终止生成过程
            if isinstance(chunk, dict) and "error" in chunk:
                yield f"data: {json.dumps({'error': chunk['error']}, ensure_ascii=False)}\n\n"
                break
            
            # 仅处理 (BaseMessage, metadata) 元组格式的AIMessageChunk
            if isinstance(chunk, (list, tuple)):
                msg, meta = chunk[0], chunk[1]
                if (not isinstance(meta, dict)) or (not isinstance(msg, AIMessage)):
                    continue

                final_text = _message_to_text(msg)
                if final_text:
                    yield f"data: {json.dumps({'text': final_text}, ensure_ascii=False)}\n\n"

    except Exception as e:
        logging.error(f"chat_stream_generator 方法生成回答过程中出现异常: {e}")
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    finally:
        # 确保后台任务结束（若仍在运行则取消）
        if task and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        yield "data: [DONE]\n\n"


# 定义chat接口，用于接收用户消息并返回模型生成的回答，使用SSE协议实现流式响应
@app.post("/chat")
async def chat_endpoint(request_data: ChatRequest):
    return StreamingResponse(
                content=chat_stream_generator(request_data), 
                media_type="text/event-stream"
            )


# 定义一个接口，用于清除指定 analysis_id 的会话上下文
@app.delete("/chat/clear-session/{analysis_id}")
async def clear_session(analysis_id: str):
    if analysis_id in sessions_context_register:
        try:
            del sessions_context_register[analysis_id]
            logging.info(f"用户断开连接，已清除 analysis_id: {analysis_id} 的会话资源。")
            logging.info(f"当前剩余活跃会话数: {len(sessions_context_register)}")
            return {"status": "success", "message": f"Session {analysis_id} cleared"}
        except Exception as e:
            logging.error(f"清除 analysis_id: {analysis_id} 的会话资源时出错: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"status": "not_found", "message": "Session not found"}


if __name__ == "__main__":
    # 启动 FastAPI 应用，监听端口 7860
    uvicorn.run(app, host="0.0.0.0", port=7860)
