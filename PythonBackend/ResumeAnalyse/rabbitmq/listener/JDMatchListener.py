from pika.adapters.blocking_connection import BlockingConnection

from ResumeAnalyse.rabbitmq.constants import JD_MATCH_REQUEST_QUEUE_NAME
from ResumeAnalyse.rabbitmq.listener.callback.MatchCallback import jd_match_callback
from ResumeAnalyse.rabbitmq.utils import mq_parameters

# 创建RabbitMQ的连接实例
# rabbitmq_connection = BlockingConnection(mq_parameters)


def create_jd_match_listener():
    rabbitmq_connection = BlockingConnection(mq_parameters)
    channel = rabbitmq_connection.channel()
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=JD_MATCH_REQUEST_QUEUE_NAME,
        on_message_callback=jd_match_callback,
        auto_ack=False      # 采用手动确认，确保消息在处理完成后才被确认
    )
    print(' [*] `JD Match Listener` is waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    # 停止监听器，关闭连接
    rabbitmq_connection.close()


if __name__ == "__main__":
    create_jd_match_listener()
