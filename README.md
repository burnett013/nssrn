# Nursing Workforce Data Dashboard

A full-stack analytics dashboard to explore the **2022 National Sample Survey of Registered Nurses (NSSRN)**. This project provides insights into the nursing workforce, focusing on burnout, earnings, job satisfaction, and telehealth adoption.

## Project Overview

This tool processes raw fixed-width survey data (SAS/TXT format) into a structured SQLite database and serves aggregated, weighted statistics via a REST API to an interactive frontend dashboard.

**Key Questions Answered:**
*   How does nurse burnout vary by state and work setting?
*   What is the relationship between education level/gender and earnings?
*   How widely adopted is telehealth in the nursing profession?
*   How does job satisfaction differ between genders?
*   What is the breakdown of telehealth users by nurse type (RN vs NP)?

## Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│             │      │             │      │             │
│  Streamlit  │ ───→ │     API     │ ───→ │  Database   │
│  Dashboard  │ ←─── │  (FastAPI)  │ ←─── │  (SQLite)   │
│             │      │             │      │             │
└─────────────┘      └─────────────┘      └─────────────┘
  (Frontend)         (Backend)           (Data Storage)
  Port 8501          Port 8001           nursing.db
```

### How The Components Work Together

#### 1. **Database (SQLite - `nursing.db`)**
- **Role**: Stores all the raw nursing workforce data
- **Size**: ~201 MB of survey data
- **Think of it as**: A giant filing cabinet with all your survey responses

#### 2. **API (FastAPI - `api/main.py`)**
- **Role**: Fetches data from the database and calculates statistics
- **Runs on**: `http://localhost:8001`
- **Think of it as**: A smart assistant that knows how to find and analyze data
- **Endpoints**:
  - `/burnout` - Burnout statistics
  - `/satisfaction` - Job satisfaction (with optional gender breakdown)
  - `/earnings` - Earnings by various groupings
  - `/telehealth` - Telehealth adoption overall
  - `/telehealth/by_nurse_type` - Telehealth users by RN vs NP
  - `/telehealth/by_gender` - Telehealth users by gender

#### 3. **Streamlit Dashboard (`dashboard.py`)**
- **Role**: Interactive web interface for data visualization
- **Runs on**: `http://localhost:8501`
- **Think of it as**: The front desk/display window
- **Features**: State filtering, interactive charts, gender breakdowns

### Example Data Flow

When you select **"Texas"** from the state filter to see telehealth usage:

1. **You interact** with the Streamlit dashboard (select "Texas")
2. **Streamlit sends request** to API: `GET http://localhost:8001/telehealth?state=TX`
3. **API queries database**:
   ```sql
   SELECT PN_TELHLTH, SUM(RKRNWGTA) 
   FROM nssrn 
   WHERE STATE_PUF = 'TX'
   GROUP BY PN_TELHLTH
   ```
4. **Database returns** raw results to API
5. **API processes** data (calculates percentages)
6. **API sends back** clean JSON data to Streamlit
7. **Streamlit creates** a beautiful chart and displays it

**Restaurant Analogy**:
- Database = Kitchen storage/pantry
- API = Chef who prepares the food
- Streamlit = Waiter who presents it nicely to you

## Tech Stack

*   **ETL**: Python (Pandas) to parse SAS schemas and load fixed-width text files
*   **Database**: SQLite for lightweight, relational data storage
*   **Backend**: FastAPI for serving RESTful API endpoints
*   **Frontend**: Streamlit for interactive data visualization (Charts via Altair)
*   **Design**: UT Tyler brand colors (Orange #BF5700 & Blue #003F87)

## Features

*   **Weighted Analysis**: All statistics use the survey's weighted sample (`RKRNWGTA`) to represent the national workforce accurately
*   **Interactive Filters**: Filter dashboards by State
*   **Earnings Analysis**: Group average earnings by Work Setting, Age, Degree, or Gender
*   **Gender Breakdown**: Job satisfaction can be broken down by gender
*   **Telehealth Analytics**: Overall adoption + breakdowns by nurse type and gender
*   **Visualizations**: Clean bar charts, donut charts, and clustered charts with human-readable labels

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
*This creates `nursing.db` (~201 MB with 49k rows).*

### 4. Running the Application

**Recommended: Use the startup script**
```bash
./run.sh
```

This script automatically:
1. Starts the API server on port 8001
2. Waits 3 seconds for the API to initialize
3. Starts the Streamlit dashboard on port 8501
4. Cleans up both processes when you stop the dashboard

**Manual Option: Run Components Separately**

Terminal 1 - Start the Backend API:
```bash
python3 -m api.main
```

Terminal 2 - Start the Frontend Dashboard:
```bash
streamlit run dashboard.py
```

Open your browser to `http://localhost:8501`.

### 5. Validation
To run quick queries against the raw text file for verification:
```bash
python3 val.py
```

## Troubleshooting

**Issue: "No data available" in new charts**
- Solution: Clear Streamlit cache (press `C` in the dashboard or use the hamburger menu)

**Issue: API endpoints not found**
- Solution: Restart the API server to load new endpoints

**Issue: Port already in use**
- Solution: Kill the process using the port:
  ```bash
  lsof -ti :8001 | xargs kill -9  # For API
  lsof -ti :8501 | xargs kill -9  # For Streamlit
  ```

## Data Source
*   **2022 National Sample Survey of Registered Nurses (NSSRN)**
*   U.S. Department of Health and Human Services, Health Resources and Services Administration (HRSA)

