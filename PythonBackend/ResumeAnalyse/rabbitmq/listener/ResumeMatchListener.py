from pika.adapters.blocking_connection import BlockingConnection

from ResumeAnalyse.rabbitmq.constants import RESUME_MATCH_REQUEST_QUEUE_NAME
from ResumeAnalyse.rabbitmq.listener.callback.MatchCallback import resume_match_callback
from ResumeAnalyse.rabbitmq.utils import mq_parameters

# 创建RabbitMQ的连接实例
# rabbitmq_connection = BlockingConnection(mq_parameters)


def create_resume_match_listener():
    with BlockingConnection(mq_parameters) as rabbitmq_connection:
        channel = rabbitmq_connection.channel()
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=RESUME_MATCH_REQUEST_QUEUE_NAME,
            on_message_callback=resume_match_callback,
            auto_ack=False      # 采用手动确认，确保消息在处理完成后才被确认
        )
        print(' [*] `Resume Match Listener` is waiting for messages. To exit press CTRL+C')
        channel.start_consuming()


if __name__ == "__main__":
    create_resume_match_listener()
