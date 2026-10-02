# Trevolk Forecasting Engine

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

## Overview

The Trevolk Forecasting Engine is a production-grade B2B SaaS application designed for dynamic sales prediction and demand forecasting. It leverages an XGBoost regression model served via a high-performance FastAPI backend, paired with a modern React frontend for real-time visualization of key performance indicators (KPIs) and operational insights.

## Key Features

- **Modular Backend Architecture:** Clean separation of concerns with dedicated layers for API routing, Pydantic schema validation, and core business logic.
- **Singleton ML Inference:** Thread-safe, memory-efficient lazy loading of the XGBoost model for 7-day rolling batch predictions.
- **Modern SaaS UI:** A clean, light-mode frontend built with React, Vite, and Tailwind CSS, featuring interactive Recharts and fluid Framer Motion animations.
- **DevSecOps Automation:** Integrated AST-based security linting (Bandit), dependency vulnerability scanning (Safety), and automated PDF architecture documentation generation.

## Repository Structure

```text
Trevolk_Forecasting_Engine/
├── app/                        # Backend Application
│   ├── api/                    # API Routers & Endpoints
│   ├── schemas/                # Pydantic Request/Response Models
│   ├── services/               # ML Inference & Business Logic (Singleton)
│   └── main.py                 # FastAPI Entry Point & CORS Setup
├── frontend/                   # Frontend Application (React/Vite)
├── generate_pdf_docs.py        # Automated PDF Documentation Generator
├── ship_it.py                  # Master DevSecOps Automation Pipeline
├── deploy_git.py               # Deployment Helper Script
├── requirements.txt            # Backend Dependencies
└── README.md                   # Project Documentation
```

## Local Setup & Installation

### ⚠️ Critical Note on Security & Large Files
> To adhere to security best practices and repository size limits, the `trevolk_sales_model.pkl` (77MB) and `.env` files are strictly excluded via `.gitignore`. 
> 
> **You must provide your own trained XGBoost model (`trevolk_sales_model.pkl`) and place it in the root directory before starting the backend server.**

### Backend Initialization

1. Clone the repository:
   ```bash
   git clone https://github.com/musa8868973-web/trevolk-forecast-engine.git
   cd trevolk-forecast-engine
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure your model is present and start the Uvicorn server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Initialization

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   bun install
   ```

3. Start the development server:
   ```bash
   npm run dev
   # or
   bun dev
   ```

## DevSecOps Pipeline

This repository includes a dedicated automation script (`ship_it.py`) for managing the CI/CD and documentation lifecycle prior to deployment. 

To execute the pipeline:
```bash
python ship_it.py
```
This script automatically orchestrates:
1. **Security Scanning:** Executes `bandit` and `safety` to verify code integrity and dependency safety.
2. **Documentation:** Triggers `generate_pdf_docs.py` (via ReportLab) to produce an up-to-date architectural PDF.
3. **Version Control:** Stages, commits, and pushes to the remote repository.
4. **Server Launch:** Starts the local FastAPI development server.

## License / Copyright

Copyright © Trevolk - All Rights Reserved.
