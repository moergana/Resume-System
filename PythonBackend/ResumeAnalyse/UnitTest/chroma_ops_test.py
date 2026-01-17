import unittest
from ResumeAnalyse.Vectorizer import resume_vectordb, JD_vectordb


class WorkflowTestCase(unittest.TestCase):
    def test_resume_db_delete_by_id(self):
        resume_vectordb.delete(ids=["jd_test_1"])
        res = resume_vectordb.get(ids=["jd_test_1"])
        print(res)
        
    def test_JD_db_delete_by_id(self):
        JD_vectordb.delete(ids=["jd_test_1"])


if __name__ == '__main__':
    unittest.main()
