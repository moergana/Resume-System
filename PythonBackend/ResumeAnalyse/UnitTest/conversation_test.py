import asyncio
import contextlib
import logging
import unittest

import gradio
from langchain_core.messages import AIMessage

from ResumeAnalyse.Conversation import _message_to_text, invoke_agent_in_background, sessions_context_register, \
    init_conversation_agent, mock_data
from ResumeAnalyse.entity.thread_local import thread_resume_summary_text, thread_jd_summary_text, thread_match_score, \
    thread_resume_advice, thread_job_hunting_advice


async def chat_with_agent(message: str, history: list, request: gradio.Request):
    """
    Gradio 回调：启动后台任务并消费队列，yield 给前端。
    :param message: 用户输入的消息
    :param history: 对话历史
    :return: 异步生成器，yield 流式输出块
    """
    # 获取当前用户的唯一会话 ID (对应浏览器的一个 Tab)
    session_id = request.session_hash
    logging.info(f"收到用户消息，Session ID: {session_id}")

    # 判断对话智能体是否已经被初始化。如果没有就调用init_conversation_agent
    # 需要注意init_conversation_agent方法所需的参数从thread_local中获取
    if session_id not in sessions_context_register:
        logging.error("对话智能体尚未初始化!")

        # --- 数据获取逻辑 ---
        # 注意：在真实场景中，简历数据应该在之前的步骤（如上传简历）中已经存入 sessions_context_register
        # 这里为了演示，如果字典里没有数据，我们先用 mock_data 填充
        # 实际上你应该在解析简历的函数中，也通过 request.session_hash 将数据存入 sessions_context_register

        # 模拟获取数据 (你可以保留 thread_local 用于 mock_data 的临时生成，或者直接在这里定义变量)
        mock_data()  # 测试时使用mock数据，正式环境请移除这行

        logging.info("对话智能体尚未初始化，正在初始化...")
        # logging.info(f"简历摘要文本: {thread_resume_summary_text.get()}")
        # logging.info(f"职位描述摘要文本: {thread_jd_summary_text.get()}")
        # logging.info(f"匹配度分数: {thread_match_score.get()}")
        # logging.info(f"简历改进建议: {thread_resume_advice.get()}")
        # logging.info(f"求职建议: {thread_job_hunting_advice.get()}")

        agent, config = await init_conversation_agent(
            resume_summary_text=thread_resume_summary_text.get(),
            jd_summary_text=thread_jd_summary_text.get(),
            match_score=thread_match_score.get(),
            improvement_suggestions=thread_resume_advice.get(),
            job_hunting_advice=thread_job_hunting_advice.get(),
        )

        # 将 Agent 和 Config 存入全局字典，实现持久化
        sessions_context_register[session_id] = {
            "conversation_agent": agent,
            "conversation_config": config
        }
        logging.info("对话智能体初始化完成。")

    # 从全局字典中获取当前用户的 Agent 和 Config
    user_context = sessions_context_register[session_id]
    conversation_agent = user_context["conversation_agent"]
    config = user_context["conversation_config"]

    queue = asyncio.Queue()

    # 启动后台任务（不要await，应该用asyncio开启一个新的后台任务）
    task = asyncio.create_task(invoke_agent_in_background(queue, message, conversation_agent, config))

    full_response = ""

    # 如果你不想占位文本，可以移除下面两行，但务必在结束前确保至少 yield 一次。
    placeholder = "正在处理，请稍候..."
    yield placeholder
    output_once = False

    try:
        while True:
            chunk = await queue.get()

            # 结束信号
            if chunk is None:
                if not output_once:
                    # 若没有任何产出，最后至少返回一句，避免 StopAsyncIteration
                    yield "抱歉，没有产生可显示的输出。"
                break

            # 错误通道
            if isinstance(chunk, dict) and "error" in chunk:
                yield f"抱歉，处理时出现错误: {chunk['error']}"
                break

            # 仅处理形如 (BaseMessage, metadata) 的AIMessage流块
            if isinstance(chunk, (list, tuple)):
                msg, meta = chunk[0], chunk[1]
                if (not isinstance(meta, dict)) or (not isinstance(msg, AIMessage)):
                    continue

                final_text = _message_to_text(msg)
                if final_text:
                    full_response += final_text
                    yield full_response
                    output_once = True

    finally:
        # 确保后台任务结束（若仍在运行则取消）
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


# 自定义CSS样式
# 使用多行字符串可以方便地编写CSS
custom_css = """
/* 将整个页面的背景设置为深灰色 */
body {
    background-color: #2b2b2b !important;
}

/* 强制将标题文字颜色设置为白色 */
.gradio-container h1.gr-title {
    color: white !important;
}

/* (可选) 将描述文字颜色也设置为浅灰色，且位置居中，以提高可读性 */
.gradio-container .gr-description p {
    color: #f0f0f0 !important;
    text-align: center !important;
}
"""


class ConversationTestCase(unittest.TestCase):
    def test_mock_data_conversation(self):
        # --- Gradio 界面 ---
        demo = gradio.ChatInterface(
            fn=chat_with_agent,
            title="🤖 简历分析求职助理",
            description="一个基于多智能体架构的求职助手，能够帮助你分析简历和职位描述，提供有价值的建议和指导。",
            examples=[
                ["我的简历与目标岗位匹配度较低，是否应该调整目标？"],
                ["根据我的简历，推荐一下适合我投递的公司"],
                ["根据我的简历和目标职位描述，你觉得我在面试中需要注意哪些方面？"],
            ],
            theme="gradio/dark",  # 1. 先设置一个好的暗色主题作为基础
            css=custom_css,  # 2. 再用自定义CSS进行自定义
        )

        # 启动 Gradio 应用，监听所有网络接口
        demo.launch(server_name="0.0.0.0")


if __name__ == '__main__':
    unittest.main()
