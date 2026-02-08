from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import (
    DocumentConverter,
    ImageFormatOption,
    PdfFormatOption,
    PowerpointFormatOption,
    WordFormatOption,
)

from ResumeAnalyse.constants import DOC_FILE_SUFFIX, DOCX_FILE_SUFFIX, IMAGE_FILE_SUFFIX_LIST, PDF_FILE_SUFFIX, PPT_FILE_SUFFIX, PPTX_FILE_SUFFIX


def get_pdfpipeline_options() -> PdfPipelineOptions:
    """
    获取PDF文档解析的配置选项
    :return: PdfPipelineOptions对象
    """
    # Docling Parse with EasyOCR (default)
    # -------------------------------
    # Enables OCR and table structure with EasyOCR, using automatic device
    # selection via AcceleratorOptions. Adjust languages as needed.

    # Initialize PdfPipelineOptions
    pipeline_options = PdfPipelineOptions()
    # enable OCR
    pipeline_options.do_ocr = True
    # enable table structure detection
    pipeline_options.do_table_structure = True
    # choose languages for OCR. It needs to specify manually because the default is only English.
    # Spported languages: English, Simplified Chinese, Traditional Chinese, Japanese, Korean, Spanish, Russian
    pipeline_options.ocr_options.lang = ["en", "ch_sim", "ch_tra", "jp", "ko", "es", "ru"]
    # set the number of threads and device for OCR. AUTO means automatic selection.
    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=4, device=AcceleratorDevice.AUTO
    )
    return pipeline_options


def pdf_to_markdown(file_path: str) -> str:
    """
    Convert a PDF file to Markdown format using Docling.
    :param file_path: Path to the PDF file
    :return: Converted Markdown content as a string
    """
    # get pdf pipeline options object
    pipeline_options = get_pdfpipeline_options()

    # Create DocumentConverter with PDF format options
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    # Convert the PDF to a Document(Type is "DoclingDocument")
    doc = doc_converter.convert(file_path).document
    # Export the Document to Markdown
    return doc.export_to_markdown()


def docx_to_markdown(file_path: str) -> str:
    """
    Convert a DOCX file to Markdown format using Docling.
    :param file_path: Path to the DOCX file
    :return: Converted Markdown content as a string
    """
    # get pdf pipeline options object
    pipeline_options = get_pdfpipeline_options()

    # Create DocumentConverter with DOCX format options
    # Tips: DOCX files are analysed mainly by python-docx, OCR may not be used.
    #       But if the DOCX file contains images, OCR can be used to extract information from images.
    doc_converter = DocumentConverter(
        format_options={InputFormat.DOCX: WordFormatOption(pipeline_options=pipeline_options)}
    )
    # Convert the DOCX to a Document(Type is "DoclingDocument")
    doc = doc_converter.convert(file_path).document
    # Export the Document to Markdown
    return doc.export_to_markdown()


def pptx_to_markdown(file_path: str) -> str:
    """
    Convert a PPTX file to Markdown format using Docling.
    :param file_path: Path to the PPTX file
    :return: Converted Markdown content as a string
    """
    # get pdf pipeline options object
    pipeline_options = get_pdfpipeline_options()

    # Create DocumentConverter with PPTX format options
    # Tips: PPTX files are analysed mainly by python-pptx, OCR may not be used.
    #       But if the PPTX file contains images, OCR can be used to extract information from images.
    doc_converter = DocumentConverter(
        format_options={InputFormat.PPTX: PowerpointFormatOption(pipeline_options=pipeline_options)}
    )
    # Convert the PPTX to a Document(Type is "DoclingDocument")
    doc = doc_converter.convert(file_path).document
    # Export the Document to Markdown
    return doc.export_to_markdown()


def pic_to_markdown(file_path: str) -> str:
    """
    Convert an image file (PNG, JPEG, TIFF, BMP, WEBP) to Markdown format using Docling.
    :param file_path: Path to the image file
    :return: Converted Markdown content as a string
    """
    # Configure pipeline options similar to PDF processing
    pipeline_options = get_pdfpipeline_options()

    # Create DocumentConverter with Image format options
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options)
        }
    )
    # Convert the Image to a Document(Type is "DoclingDocument")
    doc = doc_converter.convert(file_path).document
    # Export the Document to Markdown
    return doc.export_to_markdown()


def extract_file_to_markdown(file_path: str):
    """
    Convert a file to Markdown format using Docling.
    :param file_path: Path to the file
    :return: Converted Markdown content as a string
    """
    # check file suffix and convert to markdown using corresponding function
    if file_path.lower().endswith(PDF_FILE_SUFFIX):
        return pdf_to_markdown(file_path)

    elif file_path.lower().endswith(DOC_FILE_SUFFIX) or file_path.lower().endswith(DOCX_FILE_SUFFIX):
        return docx_to_markdown(file_path)

    elif file_path.lower().endswith(PPT_FILE_SUFFIX) or file_path.lower().endswith(PPTX_FILE_SUFFIX):
        return pptx_to_markdown(file_path)
    
    elif file_path.lower().endswith(tuple(IMAGE_FILE_SUFFIX_LIST)):
        return pic_to_markdown(file_path)
    
    else:
        raise ValueError("Unsupported file format")


if __name__ == "__main__":
    source = "/root/program_projects/LangGraph/Resume_Data/sample/resume_sample_20200120/pdf/cbb7a43eb62f.pdf"  # file path or URL
    markdown_res = extract_file_to_markdown(source)
    print(markdown_res)  # output: "### Docling Technical Report[...]"
