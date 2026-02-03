from pika.adapters.blocking_connection import BlockingConnection

from ResumeAnalyse.rabbitmq.constants import JD_DELETE_QUEUE_NAME
from ResumeAnalyse.rabbitmq.listener.callback.DeleteCallback import jd_delete_callback
from ResumeAnalyse.rabbitmq.utils import mq_parameters, aio_mq_parameters
from aio_pika import connect_robust


def create_jd_delete_listener():
    # 建立与 RabbitMQ 的连接。使用with语句确保连接在使用后正确关闭
    with BlockingConnection(mq_parameters) as rabbitmq_connection:
        channel = rabbitmq_connection.channel()
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=JD_DELETE_QUEUE_NAME,
            on_message_callback=jd_delete_callback,  # 这里需要填入实际的回调函数
            auto_ack=False      # 采用手动确认，确保消息在处理完成后才被确认
        )
        print(' [*] `Resume Delete Listener` is waiting for messages. To exit press CTRL+C')
        channel.start_consuming()


if __name__ == "__main__":
    create_jd_delete_listener()
