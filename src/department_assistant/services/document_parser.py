# src/department_assistant/services/document_parser.py
import io
from pathlib import Path
from docx import Document
from pypdf import PdfReader

def _split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """Простая функция для разбивки текста на чанки с перекрытием."""
    if not text:
        return []
    
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(text)

def parse_document(file_path: Path, file_content: bytes) -> list[str]:
    """Парсит файл и возвращает список текстовых чанков."""
    text = ""
    if file_path.suffix == '.pdf':
        reader = PdfReader(io.BytesIO(file_content))
        for page in reader.pages:
            text += page.extract_text() + "\n"
    elif file_path.suffix == '.docx':
        doc = Document(io.BytesIO(file_content))
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file_path.suffix == '.txt':
        text = file_content.decode('utf-8')
    else:
        # Неподдерживаемый тип файла
        return []
        
    return _split_text_into_chunks(text)