import unittest

from sqlalchemy import create_engine, text

from ResumeAnalyse.utils import MYSQL_DB_URL


class MySQLTestCase(unittest.TestCase):
    def __init__(self):
        super().__init__()
        self.engine = create_engine(MYSQL_DB_URL)

    def test_connection(self):
        """Test MySQL database connection."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                self.assertEqual(result.scalar(), 1)
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_get_analysis_records(self):
        """Test fetching records from resume_analysis_records table."""
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
