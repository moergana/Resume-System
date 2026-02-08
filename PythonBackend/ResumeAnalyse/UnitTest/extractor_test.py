import unittest
import os

from ResumeAnalyse.Extractor import *


class ExtractorTestCase(unittest.TestCase):
    def test_pdf_to_markdown(self):
        # PDF file path or URL
        source = "/mnt/e/WorkSpace/大三大四部分课程资料/大四/毕业论文/Resumes/Chinese/resume_train_20200121/pdf/0aee98c8a561.pdf"
        markdown_res = pdf_to_markdown(source)
        print(markdown_res)

    def test_docx_to_markdown(self):
        # DOCX file path or URL
        source = "/mnt/e/WorkSpace/大三大四部分课程资料/大四/毕业论文/Resumes/Chinese/resume_train_20200121/docx/0aee98c8a561.docx"
        markdown_res = docx_to_markdown(source)
        print(markdown_res)

    def test_pptx_to_markdown(self):
        # PPTX file path or URL
        source = "/mnt/e/WorkSpace/大三大四部分课程资料/大四/毕业论文/Resumes/Chinese/resume_train_20200121/pptx/0aee98c8a561.pptx"
        markdown_res = pptx_to_markdown(source)
        print(markdown_res)

    def test_pic_to_markdown(self):
        # Image file path or URL
        source_dir = "/mnt/e/WorkSpace/大三大四部分课程资料/大四/毕业论文/Resumes/Chinese/resume_train_20200121/pic/0aee98c8a561"
        # get all image files in the source_dir
        images = []
        for file_name in os.listdir(source_dir):
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp')):
                source = os.path.join(source_dir, file_name)
                images.append(source)

        # convert each image to markdown
        for image in images:
            markdown_res = pic_to_markdown(image)
            print(markdown_res)


if __name__ == '__main__':
    unittest.main()
