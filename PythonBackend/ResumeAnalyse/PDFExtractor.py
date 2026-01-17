from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption


def pdf_to_markdown(file_path: str) -> str:
    # Docling Parse with EasyOCR (default)
    # -------------------------------
    # Enables OCR and table structure with EasyOCR, using automatic device
    # selection via AcceleratorOptions. Adjust languages as needed.
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.ocr_options.lang = ["es"]
    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=4, device=AcceleratorDevice.AUTO
    )

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


if __name__ == "__main__":
    source = "/root/program_projects/LangGraph/Resume_Data/sample/resume_sample_20200120/pdf/cbb7a43eb62f.pdf"  # file path or URL
    markdown_res = pdf_to_markdown(source)
    print(markdown_res)  # output: "### Docling Technical Report[...]"
