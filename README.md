# ATS & Scraper Pro - AI-Powered Resume Suite

ATS & Scraper Pro is a professional Windows Desktop application designed to bridge the gap between candidates and opportunities. Originally conceived as a web API, the project pivoted to a **Desktop-First Architecture** to overcome cloud-hosting limitations and provide high-performance, multi-platform job scraping directly from the user's machine.

## Key Features

- **Professional Desktop UI**: A sleek, centered window with a custom animated HTML splash screen.
- **AI Scoring Engine**: Advanced semantic matching using TF-IDF to score resumes against complex job descriptions.
- **Automated Multi-Platform Sourcing**: Upload a resume to trigger concurrent job scraping across LinkedIn, Indeed, Naukri, Glassdoor, Internshala, and more.
- **Secure Data Handling**: All resumes, job results, and databases are stored locally in the user's `%LOCALAPPDATA%` folder for maximum privacy and performance.
- **Standalone Installer**: Comes with a dedicated Windows Installer (`.exe`) for a seamless setup experience.

## Technology Stack

- **Core**: Python 3.11+
- **Backend**: FastAPI (Localhost server)
- **Scraping**: Playwright with Stealth (Bypasses advanced bot detection)
- **Frontend**: React, Vite, Tailwind CSS, and shadcn/ui
- **Packaging**: PyInstaller (onedir mode)
- **Installer**: Inno Setup

## Packaging & Installation

### For Users
1. Download the latest `ATS_Scraper_Setup.exe`.
2. Run the installer and follow the on-screen instructions.
3. Launch "ATS & Scraper" from your Desktop or Start Menu.

### For Developers (Building the EXE)
1. Install dependencies: `pip install -r requirements.txt`.
2. Generate the application folder:
   ```powershell
   pyinstaller ATS_Pro.spec --noconfirm
   ```
3. Use **Inno Setup** to compile `ats_installer.iss` into the final `Setup.exe`.

## Project Structure

- `backend/`: Core logic, FastAPI server, and AI services.
- `frontend/`: React source code (Built and served by the backend).
- `scripts/`: Platform-specific job scraping modules.
- `training_data/`: Datasets for AI model refinement.
- `ATS_Pro.spec`: PyInstaller configuration for directory-based distribution.
- `ats_installer.iss`: Inno Setup script for the Windows installer.

## Privacy & Security

ATS Pro prioritizes your data. Unlike web-based ATS tools, your resumes and analysis results never leave your machine (except for scraping queries sent to job portals). All persistent data is stored in:
`%LOCALAPPDATA%\ATS_Pro_AI`
