# Handles multi-format docs
from typing import List
from langchain.schema import Document
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.pptx import partition_pptx
import pytesseract
from PIL import Image
import pandas as pd

def extract_text_from_image(img_path: str) -> str:
    """OCR for images in manuals/diagrams."""
    try:
        return pytesseract.image_to_string(Image.open(img_path))
    except Exception as e:
        print(f"OCR failed: {e}")
        return ""

def load_pdf_with_tables_images(pdf_path: str) -> List[Document]:
    """Extract text, tables, and images from PDFs."""
    elements = partition_pdf(
        filename=pdf_path,
        extract_images_in_pdf=True,
        infer_table_structure=True,
        strategy="hi_res",
        ocr_languages="eng"
    )
    
    content = []
    for elem in elements:
        if elem.category == "Table":
            content.append(f"TABLE:\n{elem.text}")
        elif elem.category == "Image":
            img_text = extract_text_from_image(elem.metadata.image_path)
            content.append(f"IMAGE_DESCRIPTION:\n{img_text}")
        else:
            content.append(elem.text)
    
    return [Document(page_content="\n\n".join(content), metadata={"source": pdf_path})]

def load_docx_with_tables(docx_path: str) -> List[Document]:
    """Extract text and tables from DOCX."""
    elements = partition_docx(filename=docx_path)
    tables = [elem.text for elem in elements if elem.category == "Table"]
    text = [elem.text for elem in elements if elem.category != "Table"]
    return [Document(page_content="\n\n".join(text + [f"TABLE:\n{t}" for t in tables]), metadata={"source": docx_path})]

def load_csv_autoparts(csv_path: str) -> List[Document]:
    """Load structured car parts data."""
    df = pd.read_csv(csv_path)
    return [Document(page_content=f"CAR PARTS DATA:\n{df.to_markdown()}", metadata={"source": csv_path})]

def load_pptx_slides(pptx_path: str) -> List[Document]:
    """Extract text and notes from PPTX."""
    elements = partition_pptx(filename=pptx_path)
    return [Document(page_content="\n\n".join([elem.text for elem in elements]), metadata={"source": pptx_path})]