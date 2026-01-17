from pika.adapters.blocking_connection import BlockingConnection

from ResumeAnalyse.rabbitmq.constants import RESUME_DELETE_QUEUE_NAME
from ResumeAnalyse.rabbitmq.listener.callback.DeleteCallback import resume_delete_callback
from ResumeAnalyse.rabbitmq.utils import mq_parameters


def create_resume_delete_listener():
    rabbitmq_connection = BlockingConnection(mq_parameters)
    channel = rabbitmq_connection.channel()
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=RESUME_DELETE_QUEUE_NAME,
        on_message_callback=resume_delete_callback,  # 这里需要填入实际的回调函数
        auto_ack=False    # 采用手动确认，确保消息在处理完成后才被确认
    )
    print(' [*] `Resume Delete Listener` is waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    # 停止监听器，关闭连接
    rabbitmq_connection.close()


if __name__ == "__main__":
    create_resume_delete_listener()
