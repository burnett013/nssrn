import pandas as pd
import re
import os

# Paths
BASE_DIR = '/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/Coding_Practice/projects/nursing_workforce'
DATA_DIR = os.path.join(BASE_DIR, '2022_NSSRN_PUF_ASCII_Package')
SAS_FILE = os.path.join(DATA_DIR, 'nssrn_2022_puf_flat.sas')
TXT_FILE = os.path.join(DATA_DIR, 'nssrn_2022_puf_flat.txt')

def parse_sas_schema(sas_file_path):
    """
    Parses the SAS input statement to get variable names and column specifications.
    Returns: list of dicts with name, start, end
    """
    variables = []
    with open(sas_file_path, 'r') as f:
        lines = f.readlines()
        
    in_input = False
    pattern = re.compile(r'^\s*(\w+)\s+\$?(\d+)-(\d+)')
    
    for line in lines:
        line = line.strip()
        if line.lower().startswith('input'):
            in_input = True
            continue
        if line.strip() == ';':
            in_input = False
            
        if in_input:
            match = pattern.match(line)
            if match:
                variables.append({
                    'name': match.group(1),
                    'start': int(match.group(2)),
                    'end': int(match.group(3))
                })
    return variables

def get_dataframe(limit=None):
    """
    Reads the dataset into a Pandas DataFrame.
    limit: optional integer to limit number of rows (useful for quick testing)
    """
    variables = parse_sas_schema(SAS_FILE)
    print(f"Schema parsed. Found {len(variables)} variables.")
    
    colspecs = [(v['start']-1, v['end']) for v in variables]
    names = [v['name'] for v in variables]
    missing_values = ['L', 'M', ' ', '.']
    
    print("Reading data...")
    df = pd.read_fwf(
        TXT_FILE,
        colspecs=colspecs,
        names=names,
        na_values=missing_values,
        nrows=limit
    )
    return df

def run_custom_query():
    # Load data (remove limit=1000 to process full file)
    df = get_dataframe(limit=None)  
    print(f"Data Loaded: {len(df)} rows.")
    
    # --- YOUR QUERIES HERE ---
    
    print("\n--- Sex Distribution (1=Male, 2=Female) ---")
    print(df['SEX'].value_counts(dropna=False))
    
    print("\n--- Burnout Distribution (1=Yes, 2=No) ---")
    print(df['PN_BURNOUT'].value_counts(dropna=False))
    
    print("\n--- Average Earnings by Gender ---")
    # Clean earnings for calculation
    df['PN_EARN_PUF'] = pd.to_numeric(df['PN_EARN_PUF'], errors='coerce')
    print(df.groupby('SEX')['PN_EARN_PUF'].mean())

if __name__ == "__main__":
    run_custom_query()
