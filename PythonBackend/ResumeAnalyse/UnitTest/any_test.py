import json
import os
import unittest
import redis
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore

from ResumeAnalyse.utils import PG_DB_URL, redis_host, redis_port, redis_db, redis_decode_responses, redis_password


class MyTestCase(unittest.TestCase):
    def test_os_envs(self):
        key = os.getenv("GEMINI_API_KEY")
        print(key)
        d = {
            "GEMINI_API_KEY": key,
            "list": []
        }
        print(json.dumps(d, ensure_ascii=False, indent=2))

    def test_db_settings(self):
        # 测试PostgreSQL的配置信息是否正确
        checkpointer_cm = AsyncPostgresSaver.from_conn_string(str(PG_DB_URL))
        store_cm = AsyncPostgresStore.from_conn_string(str(PG_DB_URL))

        # 测试Redis的配置信息是否正确
        redis_pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=redis_db,
                                          decode_responses=redis_decode_responses,
                                          password=redis_password)
        redis_client = redis.Redis(connection_pool=redis_pool)

    def test_redis_connection(self):
        redis_pool = redis.ConnectionPool(host="localhost", port=6379, db=1, decode_responses=True,
                                          password="wangxin123")
        redis_client = redis.Redis(connection_pool=redis_pool)
        redis_client.set(name="test_key", value="test_value", ex=60)  # 设置一个键值对，过期时间为60秒
        value = redis_client.get("test_key")
        print("Retrieved value from Redis:", value)
        self.assertEqual(value, "test_value")

    def test_redis_ops(self):
        redis_pool = redis.ConnectionPool(host="localhost", port=6379, db=1, decode_responses=True,
                                          password="wangxin123")
        redis_client = redis.Redis(connection_pool=redis_pool)
        # 测试列表操作
        redis_client.lpush("test_list", "value1")
        redis_client.lpush("test_list", "value2")
        redis_client.expire("test_list", 60)  # 设置列表的过期时间为60秒
        list_values = redis_client.lrange("test_list", 0, -1)   # 获取整个列表(end=-1表示获取到最后一个元素)
        print("List values:", list_values)
        self.assertEqual(list_values, ["value2", "value1"])

        # 测试哈希操作
        redis_client.hset("test_hash", "field1", "hash_value1")
        redis_client.expire("test_hash", 60)  # 设置哈希的过期时间为60秒
        hash_value = redis_client.hget("test_hash", "field1")
        print("Hash value:", hash_value)
        self.assertEqual(hash_value, "hash_value1")


if __name__ == '__main__':
    unittest.main()
