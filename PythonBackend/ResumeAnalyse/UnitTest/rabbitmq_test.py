import json
import time
import unittest

from pika.adapters.blocking_connection import BlockingConnection
from pika.connection import ConnectionParameters
from pika.credentials import PlainCredentials

from ResumeAnalyse.entity.advice import Advice

test_mq_parameters = ConnectionParameters(
    host='localhost',
    port=5672,
    virtual_host="/resumesys",
    credentials=PlainCredentials(
        username='resumesys', password='resume123'
    ),
)

test_connection = BlockingConnection(test_mq_parameters)

ANALYSE_EXCHANGE_NAME = "analyse.direct"
ANALYSE_REQUEST_QUEUE_NAME = "analyse.request.queue"
ANALYSE_REQUEST_ROUTING_KEY = "analyse.request.routing"

ANALYSE_RESULT_QUEUE_NAME = "analyse.result.queue"
ANALYSE_RESULT_ROUTING_KEY = "analyse.result.routing"


def consume_callback(ch, method, properties, body):
    print("Get a message:", body.decode())
    ch.basic_publish(
        exchange=ANALYSE_EXCHANGE_NAME,
        routing_key=ANALYSE_RESULT_ROUTING_KEY,
        body=json.dumps(body.decode())
    )


class MyTestCase(unittest.TestCase):
    def test_rabbitmq_connection(self):
        channel = test_connection.channel()
        print("成功连接到 RabbitMQ 服务器并创建了一个频道。")
        channel.close()

    def test_rabbitmq_ops(self):
        channel = test_connection.channel()

        # 声明一个队列
        # queue_name = 'test_queue'
        # channel.queue_declare(queue=queue_name)

        # 发送一条消息到队列
        message = {
            "msg": ["Hello, RabbitMQ!", "It's a test message."]
        }
        channel.basic_publish(exchange=ANALYSE_EXCHANGE_NAME, routing_key=ANALYSE_REQUEST_ROUTING_KEY, body=json.dumps(message))
        print(f"已发送消息: {message}")

        # 从队列中接收消息
        method_frame, header_frame, body = channel.basic_get(queue=ANALYSE_RESULT_QUEUE_NAME, auto_ack=True)
        if method_frame:
            print(f"已接收消息: {body.decode()}")
        else:
            print("队列中没有消息。")

        # 删除队列
        # channel.queue_delete(queue=queue_name)
        # print(f"已删除队列: {queue_name}")

        channel.close()

    def test_add_listener(self):
        channel = test_connection.channel()
        channel.basic_consume(
            queue=ANALYSE_REQUEST_QUEUE_NAME,
            on_message_callback=consume_callback,
            auto_ack=True
        )
        print("开始监听队列，等待消息...")
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            print("停止监听。")
            channel.stop_consuming()
        channel.close()

    def test_publish_pydantic(self):
        advice = Advice(
            match_score=95,
            improvement_suggestions="It is a great resume overall.",
            job_hunting_tips="Keep applying to relevant positions and networking.",
        )
        channel = test_connection.channel()
        channel.basic_publish(
            exchange=ANALYSE_EXCHANGE_NAME,
            routing_key=ANALYSE_RESULT_ROUTING_KEY,
            body=advice.model_dump_json()
        )
        # time.sleep(20)
        method_frame, header_frame, body = channel.basic_get(queue=ANALYSE_RESULT_QUEUE_NAME, auto_ack=True)
        if method_frame:
            content = body.decode()
            print(f"已接收消息: {content}")
            get_advice = Advice.model_validate_json(content)
            print(type(get_advice))
            print(get_advice)

        else:
            print("队列中没有消息。")
        channel.close()

    def test(self):
        msg = {
            "id": 123
        }
        msg["id"] = str(msg["id"])
        print(json.dumps(msg))
        channel = test_connection.channel()
        channel.basic_publish(
            exchange=ANALYSE_EXCHANGE_NAME,
            routing_key=ANALYSE_RESULT_ROUTING_KEY,
            body=json.dumps(msg)
        )
        channel.close()


if __name__ == '__main__':
    unittest.main()
