from pika.adapters.blocking_connection import BlockingConnection

from ResumeAnalyse.rabbitmq.constants import *
from ResumeAnalyse.rabbitmq.listener.callback.ResumeAnalyseCallback import resume_analyse_callback
from ResumeAnalyse.rabbitmq.utils import mq_parameters

# 创建RabbitMQ的连接实例
# rabbitmq_connection = BlockingConnection(mq_parameters)


def create_resume_analyse_listener():
    # 建立与 RabbitMQ 的连接。使用with语句确保连接在使用后正确关闭
    with BlockingConnection(mq_parameters) as rabbitmq_connection:
        channel = rabbitmq_connection.channel()
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=ANALYSE_REQUEST_QUEUE_NAME,
            on_message_callback=resume_analyse_callback,
            auto_ack=False    # 采用手动确认，确保消息在处理完成后才被确认
        )
        print(' [*] `Resume Analyse Listener` is waiting for messages. To exit press CTRL+C')
        channel.start_consuming()


if __name__ == "__main__":
    create_resume_analyse_listener()
