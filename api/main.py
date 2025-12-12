from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import pandas as pd
import os
from typing import List, Optional
import logging

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nursing Workforce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "nursing.db")

def get_data(query: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        logger.info(f"Executing query: {query}")
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/")
def read_root():
    return {"message": "Nursing Workforce API is running"}

@app.get("/filter_options")
def get_filter_options():
    # Using STATE_PUF for state
    states_query = "SELECT DISTINCT STATE_PUF FROM nssrn ORDER BY STATE_PUF"
    settings_query = "SELECT DISTINCT PN_EMPSIT FROM nssrn ORDER BY PN_EMPSIT" 
    
    states = get_data(states_query)['STATE_PUF'].dropna().tolist()
    settings = get_data(settings_query)['PN_EMPSIT'].dropna().tolist()
    return {
        "states": states,
        "work_settings": settings
    }

@app.get("/burnout")
def get_burnout_stats(state: Optional[str] = None):
    # Use CAST to ensure numeric summation works
    where_clause = "WHERE 1=1"
    if state:
        where_clause += f" AND STATE_PUF = '{state}'"
        
    query = f"""
        SELECT 
            PN_BURNOUT as category,
            SUM(CAST(RKRNWGTA AS REAL)) as weighted_count
        FROM nssrn
        {where_clause}
        GROUP BY PN_BURNOUT
    """
    df = get_data(query)
    
    # Fill NaN categories if any (though grouping usually handles it)
    df = df.dropna(subset=['category'])
    
    total = df['weighted_count'].sum()
    if total > 0:
        df['percentage'] = (df['weighted_count'] / total) * 100
    else:
        df['percentage'] = 0
        
    return df.to_dict(orient="records")

@app.get("/satisfaction")
def get_satisfaction_stats(state: Optional[str] = None, breakdown_by_gender: bool = False):
    logger.info(f"get_satisfaction_stats called with state={state}, breakdown_by_gender={breakdown_by_gender}")
    # Variable: PN_SATISFD
    where_clause = "WHERE 1=1"
    if state:
        where_clause += f" AND STATE_PUF = '{state}'"
    
    # If breaking down by gender, include SEX in query
    if breakdown_by_gender:
        query = f"""
            SELECT 
                PN_SATISFD as category,
                SEX as gender,
                SUM(CAST(RKRNWGTA AS REAL)) as weighted_count
            FROM nssrn
            {where_clause}
            GROUP BY PN_SATISFD, SEX
        """
        df = get_data(query)
        df = df.dropna(subset=['category', 'gender'])
        
        # Calculate percentage within each gender
        # First get totals per gender
        gender_totals = df.groupby('gender')['weighted_count'].transform('sum')
        df['percentage'] = (df['weighted_count'] / gender_totals) * 100
        
        return df.to_dict(orient="records")
    else:
        query = f"""
            SELECT 
                PN_SATISFD as category,
                SUM(CAST(RKRNWGTA AS REAL)) as weighted_count
            FROM nssrn
            {where_clause}
            GROUP BY PN_SATISFD
        """
        df = get_data(query)
        df = df.dropna(subset=['category'])
        
        total = df['weighted_count'].sum()
        if total > 0:
            df['percentage'] = (df['weighted_count'] / total) * 100
        else:
            df['percentage'] = 0
            
        return df.to_dict(orient="records")

@app.get("/earnings")
def get_earnings_stats(state: Optional[str] = None, grouping: str = "PN_EMPSIT"):
    valid_groupings = ["PN_EMPSIT", "AGE_GP_PUF", "HIGHEDU_PUF", "SEX"]
    if grouping not in valid_groupings:
        grouping = "PN_EMPSIT"
        
    where_clause = "WHERE CAST(PN_EARN_PUF AS REAL) > 0"
    if state:
        where_clause += f" AND STATE_PUF = '{state}'"
        
    query = f"""
        SELECT 
            {grouping} as group_name,
            SUM(CAST(PN_EARN_PUF AS REAL) * CAST(RKRNWGTA AS REAL)) / SUM(CAST(RKRNWGTA AS REAL)) as avg_earnings,
            SUM(CAST(RKRNWGTA AS REAL)) as population_size
        FROM nssrn
        {where_clause}
        GROUP BY {grouping}
    """
    df = get_data(query)
    # Drop rows with null grouping
    df = df.dropna(subset=['group_name'])
    return df.to_dict(orient="records")

@app.get("/telehealth")
def get_telehealth_stats(state: Optional[str] = None):
    where_clause = "WHERE 1=1"
    if state:
        where_clause += f" AND STATE_PUF = '{state}'"
        
    query = f"""
        SELECT 
            PN_TELHLTH as category,
            SUM(CAST(RKRNWGTA AS REAL)) as weighted_count
        FROM nssrn
        {where_clause}
        GROUP BY PN_TELHLTH
    """
    df = get_data(query)
    df = df.dropna(subset=['category'])
    
    total = df['weighted_count'].sum()
    if total > 0:
        df['percentage'] = (df['weighted_count'] / total) * 100
    
    return df.to_dict(orient="records")

@app.get("/telehealth/by_nurse_type")
def get_telehealth_by_nurse_type(state: Optional[str] = None):
    """Breakdown of telehealth usage among those who USE telehealth (PN_TELHLTH=1) by RN vs NP"""
    where_clause = "WHERE PN_TELHLTH = 1"  # Only those using telehealth
    if state:
        where_clause += f" AND STATE_PUF = '{state}'"
        
    query = f"""
        SELECT 
            APN_NP as nurse_type,
            SUM(CAST(RKRNWGTA AS REAL)) as weighted_count
        FROM nssrn
        {where_clause}
        GROUP BY APN_NP
    """
    df = get_data(query)
    df = df.dropna(subset=['nurse_type'])
    
    total = df['weighted_count'].sum()
    if total > 0:
        df['percentage'] = (df['weighted_count'] / total) * 100
    
    return df.to_dict(orient="records")

@app.get("/telehealth/by_gender")
def get_telehealth_by_gender(state: Optional[str] = None):
    """Breakdown of telehealth usage among those who USE telehealth (PN_TELHLTH=1) by gender"""
    where_clause = "WHERE PN_TELHLTH = 1"  # Only those using telehealth
    if state:
        where_clause += f" AND STATE_PUF = '{state}'"
        
    query = f"""
        SELECT 
            SEX as gender,
            SUM(CAST(RKRNWGTA AS REAL)) as weighted_count
        FROM nssrn
        {where_clause}
        GROUP BY SEX
    """
    df = get_data(query)
    df = df.dropna(subset=['gender'])
    
    total = df['weighted_count'].sum()
    if total > 0:
        df['percentage'] = (df['weighted_count'] / total) * 100
    
    return df.to_dict(orient="records")

@app.get("/satisfaction/by_state")
def get_satisfaction_by_state():
    """Get satisfaction percentages for each state, focusing on Extremely Satisfied and Extremely Dissatisfied"""
    query = """
        SELECT 
            STATE_PUF as state,
            PN_SATISFD as satisfaction_level,
            SUM(CAST(RKRNWGTA AS REAL)) as weighted_count
        FROM nssrn
        WHERE STATE_PUF IS NOT NULL AND PN_SATISFD IS NOT NULL
        GROUP BY STATE_PUF, PN_SATISFD
    """
    df = get_data(query)
    
    # Calculate percentage within each state
    state_totals = df.groupby('state')['weighted_count'].transform('sum')
    df['percentage'] = (df['weighted_count'] / state_totals) * 100
    
    return df.to_dict(orient="records")

@app.get("/satisfaction/by_rural_urban")
def get_satisfaction_by_rural_urban(state: Optional[str] = None):
    """Get satisfaction by rural/urban classification for a specific state or all states"""
    where_clause = "WHERE RN_RURAL IS NOT NULL AND PN_SATISFD IS NOT NULL"
    if state:
        where_clause += f" AND STATE_PUF = '{state}'"
    
    query = f"""
        SELECT 
            RN_RURAL as area_type,
            PN_SATISFD as satisfaction_level,
            SUM(CAST(RKRNWGTA AS REAL)) as weighted_count
        FROM nssrn
        {where_clause}
        GROUP BY RN_RURAL, PN_SATISFD
    """
    df = get_data(query)
    
    # Calculate percentage within each area type
    area_totals = df.groupby('area_type')['weighted_count'].transform('sum')
    df['percentage'] = (df['weighted_count'] / area_totals) * 100
    
    return df.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
