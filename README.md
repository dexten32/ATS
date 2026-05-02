# ATS Pro - AI-Powered Resume Analysis

ATS Pro is a modern, high-performance Applicant Tracking System (ATS) utility designed to optimize resumes for AI-driven hiring workflows. It uses natural language processing and semantic matching to score resumes against job descriptions.

## Features

- **AI Scoring**: Advanced semantic matching using TF-IDF and domain-specific heuristics.
- **Resume Parsing**: Extracts skills, experience, and contact information from PDF, DOCX, and TXT files.
- **Strategic Insights**: Provides actionable feedback on candidate maturity, ownership, and technical depth.
- **Glassmorphism UI**: Beautiful, premium dark-themed interface with real-time analysis updates.
- **Security Hardened**: Built-in protections against path traversal and oversized file uploads.

## Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **Database**: SQLite with SQLAlchemy ORM
- **Machine Learning**: Scikit-Learn (TF-IDF Similarity)
- **Frontend**: React, Vite, Tailwind CSS, and shadcn/ui
- **Deployment**: Uvicorn ASGI server

## Prerequisites

- **Python 3.8+**
- (Optional) **Visual Studio Code** for the best development experience.

## Installation

1. **Clone the repository** (or download the source code).
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Backend Server**:
   From the project root directory, run:
   ```bash
   python backend/main.py
   ```
   The server will start at `http://127.0.0.1:8000`.

2. **Start the Frontend Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```
   Or build the frontend to serve it via the backend:
   ```bash
   cd frontend
   npm run build
   ```
   Then access `http://127.0.0.1:8000` to see the served frontend.

## Project Structure

- `backend/`: FastAPI application, models, routing, and scoring services.
- `frontend/`: React + Vite application with Tailwind CSS.
- `scripts/`: Standalone scripts like the LinkedIn Scraper.
- `data/`: Storage for scraped jobs and other datasets.
- `docs/`: Project documentation and overviews.
- `tests/`: Test files, load test scripts, and dummy resumes.

## Security & Maintenance

- To update dependencies: `pip install --upgrade -r requirements.txt`
- To check file audit logs, see `CHANGELOG.md`.
