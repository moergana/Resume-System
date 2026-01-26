import threading

from ResumeAnalyse.Conversation import start_bot_interface, mcp_clients, mcp_status, init_lock, init_mcp_clients
from ResumeAnalyse.rabbitmq.listener.JDMatchListener import create_jd_match_listener
from ResumeAnalyse.rabbitmq.listener.JDUploadListener import create_jd_upload_listener
from ResumeAnalyse.rabbitmq.listener.JdDeleteListener import create_jd_delete_listener
from ResumeAnalyse.rabbitmq.listener.ResumeAnalyseListener import create_resume_analyse_listener
from ResumeAnalyse.rabbitmq.listener.ResumeDeleteListener import create_resume_delete_listener
from ResumeAnalyse.rabbitmq.listener.ResumeMatchListener import create_resume_match_listener
from ResumeAnalyse.rabbitmq.listener.ResumeUploadListener import create_resume_upload_listener


def start_all_services():
    tasks = [
        create_jd_delete_listener,
        create_jd_match_listener,
        create_jd_upload_listener,
        create_resume_analyse_listener,
        create_resume_delete_listener,
        create_resume_match_listener,
        create_resume_upload_listener,
        start_bot_interface
    ]

    threads = []
    print("Starting all tasks...")

    for task in tasks:
        thread = threading.Thread(target=task)
        thread.daemon = True  # 设置为守护线程，主程序退出时自动退出
        thread.start()
        threads.append(thread)

    print(f"Started {len(threads)} tasks.")

    try:
        # 主线程保持运行，同时允许用户输入命令执行一些监控和控制
        print("""All services are running. And you can type some commands to monitor or control the services.
1. help: Show all available commands.
2. stop: Stop all services and exit the program.
3. task-list: List all running tasks.
4. check MCP status: Check the status of the MCP service.
""")
        while True:
            command = input("ResumeSystem> ")
            if command.strip().lower() == 'help':
                print("""Available commands:
1. help: Show all available commands.
2. stop: Stop all services and exit the program.
3. task-list: List all running tasks.
4. mcp-status: Check the status of the MCP service.
""")

            elif command.strip().lower() == 'task-list':
                print(f"Currently running {len(threads)} tasks:")
                for i, thread in enumerate(threads):
                    status = "running" if thread.is_alive() else "stopped"
                    print(f"  Task {i + 1}: {thread.name} - {status}")

            elif command.strip().lower() == 'stop':
                print("Stopping all services...")
                break

            elif command.strip().lower() == 'mcp-status':
                print("MCP Clients Status:")
                for status in mcp_status.items():
                    print(f"  Client {status}: {mcp_status[status]}")

            else:
                print("Unknown command. Type 'Help' for all available commands.")

    except Exception as e:
        if e == KeyboardInterrupt:
            print("Manual stopping services...")
        else:
            print(f"Exception occurred: {e}")


if __name__ == '__main__':
    start_all_services()

