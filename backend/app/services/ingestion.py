import os
import re
import shutil
import uuid
import pdfplumber
import docx
from fastapi import UploadFile, HTTPException
from typing import Tuple

import sys
if getattr(sys, 'frozen', False):
    # Safe writable path for resumes when installed in Program Files
    UPLOAD_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'ATS_Pro_AI', 'uploads')
else:
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

class IngestionService:
    @staticmethod
    def validate_file(file: UploadFile) -> str:
        # Check extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File extension {ext} not allowed")
        
        # Check size (5MB limit)
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")
        
        return ext

    @staticmethod
    def clear_uploads():
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')

    @staticmethod
    def save_file(file: UploadFile) -> str:
        # IngestionService.clear_uploads() # Commented out to allow multiple files as per new dashboard requirement
        
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)
            
        # Sanitize filename to prevent path traversal
        clean_name = "".join([c for c in file.filename if c.isalnum() or c in "._-"]).strip()
        if not clean_name:
            clean_name = "upload"
            
        unique_filename = f"{uuid.uuid4()}_{clean_name}"
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
        # 1. Remove HTML
        clean_text = re.sub(r'<[^>]*>', '', text)
        
        # 2. Fix 'Mangled' Text: Join words broken by spaces (e.g. "Skill ed" -> "Skilled")
        # Uses regex to find a letter followed by space then lowercase letter
        # but only if it's not a real word break (heuristic)
        clean_text = re.sub(r'([a-zA-Z])\s+([a-z])\b', r'\1\2', clean_text)
        
        # 3. Normalize whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()
