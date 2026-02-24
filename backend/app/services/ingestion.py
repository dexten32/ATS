import os
import shutil
import uuid
import pdfplumber
import docx
from fastapi import UploadFile, HTTPException
from typing import Tuple

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

class IngestionService:
    @staticmethod
    def validate_file(file: UploadFile) -> str:
        # Check extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File extension {ext} not allowed")
        
        # Check size (basic check)
        # file.file.seek(0, 2)
        # size = file.file.tell()
        # file.file.seek(0)
        # if size > MAX_FILE_SIZE:
        #     raise HTTPException(status_code=400, detail="File too large (max 5MB)")
        
        return ext

    @staticmethod
    def save_file(file: UploadFile) -> str:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)
            
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return file_path

    @staticmethod
    def extract_text(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == ".pdf":
                return IngestionService._extract_from_pdf(file_path)
            elif ext == ".docx":
                return IngestionService._extract_from_docx(file_path)
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    @staticmethod
    def sanitize_text(text: str) -> str:
        # Basic sanitization to prevent script injection if text is rendered
        # In a real app, this would be more complex (e.g., removing HTML tags)
        return text.strip()
