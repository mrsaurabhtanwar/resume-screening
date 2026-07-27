import os

from dotenv import load_dotenv
from docling.document_converter import DocumentConverter

load_dotenv()

def pdf_convertor_md(filepath: str):
    convertor = DocumentConverter()
    result = convertor.convert(filepath)
    md_res = result.document.export_to_markdown()
    
    return md_res
