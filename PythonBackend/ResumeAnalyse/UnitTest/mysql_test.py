import unittest

from sqlalchemy import create_engine, text

from ResumeAnalyse.utils import MYSQL_DB_URL


class MySQLTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        使用@classmethod注解修饰的setUpClass方法，该方法会在整个单元测试类执行前，仅执行一次，以提高测试效率。
        注意：
        1. setUpClass方法必须是类方法，即需要使用@classmethod注解修饰。
        2. 如果使用setUp方法，则会在每个测试方法执行前执行一次，效率较低。
        3. 不要重写__init__()方法！
        因为unittest的实例化机制是为类中的每一个测试方法都会创建一个全新的类实例。
        这意味着如果你有 5 个以 test_ 开头的方法，__init__ 就会被调用 5 次。
        另外，unittest.TestCase 的构造函数需要接收一个 methodName 参数。
        如果你重写时忘记处理这个参数或者没有正确调用 super().__init__，会导致测试框架无法正常启动，
        报出类似 TypeError: __init__() takes 1 positional argument but 2 were given 的错误。
        """
        cls.engine = create_engine(MYSQL_DB_URL)

    def test_connection(self):
        """
        测试MySQL数据库连接。
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                self.assertEqual(result.scalar(), 1)
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_get_analysis_records(self):
        """
        测试从tb_resume_analysis表中获取记录。
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    text("""SELECT * 
                            FROM tb_resume_analysis
                            WHERE id > :id
                            LIMIT 5"""),
                    {"id": 0}
                 )
                records = result.fetchall()
                self.assertIsInstance(records, list)
                for record in records:
                    print(record)
        except Exception as e:
            self.fail(f"Fetching records failed: {e}")


if __name__ == '__main__':
    unittest.main()
