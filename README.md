# Nursing Workforce Data Dashboard

A full-stack analytics dashboard to explore the **2022 National Sample Survey of Registered Nurses (NSSRN)**. This project provides insights into the nursing workforce, focusing on burnout, earnings, and telehealth adoption.

## Project Overview

This tool processes raw fixed-width survey data (SAS/TXT format) into a structured SQLite database and serves aggregated, weighted statistics via a REST API to an interactive frontend dashboard.

**Key Questions Answered:**
*   How does nurse burnout vary by state and work setting?
*   What is the relationship between education level/gender and earnings?
*   How widely adopted is telehealth in the nursing profession?

## Tech Stack

*   **ETL**: Python (Pandas) to parse SAS schemas and load fixed-width text files.
*   **Database**: SQLite for lightweight, relational data storage.
*   **Backend**: FastAPI for serving RESTful API endpoints.
*   **Frontend**: Streamlit for interactive data visualization (Charts via Altair).

## Features

*   **Weighted Analysis**: All statistics use the survey's weighted sample (`RKRNWGTA`) to represent the national workforce accurately.
*   **Interactive Filters**: Filter dashboards by State.
*   **Earnings Analysis**: Group average earnings by Work Setting, Age, Degree, or **Gender**.
*   **Visualizations**: Clean bar charts and donut charts with human-readable labels.

## Setup & Usage

### 1. Prerequisites
*   Python 3.9+
*   The 2022 NSSRN Dataset (placed in `2022_NSSRN_PUF_ASCII_Package/`)

### 2. Installation
Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. ETL (Extract, Transform, Load)
Parse the raw data and load it into the database:
```bash
python3 etl.py
```
*This creates `nursing.db` (approx 49k rows).*

### 4. Running the Application

**Option A: Run Components Separately**

Start the Backend API:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8005
```

Start the Frontend Dashboard:
```bash
streamlit run dashboard.py --server.port 8508
```

Open your browser to `http://localhost:8508`.

### 5. Validation
To run quick queries against the raw text file for verification:
```bash
python3 val.py
```

## Data Source
*   **2022 National Sample Survey of Registered Nurses (NSSRN)**
*   U.S. Department of Health and Human Services, Health Resources and Services Administration (HRSA).
