import unittest
from confluent_kafka import Consumer, Producer

class KafkaTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Kafka生产者的配置信息
        kafka_producer_config = {
            "bootstrap.servers": "localhost:9092",  # Kafka broker地址
            "batch.size": 16384,  # 批处理大小
            "linger.ms": 100,   # 等待时间
            "compression.type": "lz4",  # 压缩类型
            "acks": "all",  # 确认机制。all表示leader和所有follower都确认后才算发送成功
            "retries": 3,  # 重试次数
            "enable.idempotence": True,  # 启用幂等性。开启幂等性后，Kafka会保证消息不丢失、不重复。在Kafka 3.0+版本中默认开启
        }
        # Kafka消费者的配置信息
        kafka_consumer_config = {
            "bootstrap.servers": "localhost:9092",  # Kafka broker地址
            "group.id": "test-group",  # 消费者组ID
            "auto.offset.reset": "earliest",  # 重置偏移量的策略，当没有初始偏移量和当前偏移量不在服务器上时触发
            "enable.auto.commit": False,  # 禁用自动提交
        }
        # 创建生产者和消费者实例
        cls.producer = Producer(kafka_producer_config)
        cls.consumer = Consumer(kafka_consumer_config)

    def delivery_report(self, err, msg):
        """
        生产者发送消息后的回调函数
        :param err: 发送失败的错误信息
        :param msg: 发送的消息
        """
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

    def test_produce(self):
        """
        测试生产者
        """
        self.producer.produce(
            topic="test", 
            key="python-test".encode("utf-8"),
            value="test".encode("utf-8"),
            callback=self.delivery_report
        )
        self.producer.flush()

    def test_consumer(self):
        """
        测试消费者
        """
        # 订阅主题
        self.consumer.subscribe(["test"])
        try:
            print("Consumer started...")
            end = 10
            while end > 0:
                # 消费者尝试获取消息，超时时间为1秒
                msg = self.consumer.poll(1.0)
                if msg is None:
                    end -= 1
                    continue
                # 消息处理
                if msg.error():
                    print(f"Consumer error: {msg.error()}")
                    continue
                msg_value = msg.value()
                if msg_value is None:
                    continue
                print(f"Received message: {msg_value.decode('utf-8')}")
                # 由于关闭了自动提交，需要记得手动提交偏移量
                self.consumer.commit(asynchronous=True)
                
        except Exception as e:
            print(f"Consumer error: {e}")
        finally:
            # 关闭消费者
            self.consumer.close()

if __name__ == '__main__':
    unittest.main()