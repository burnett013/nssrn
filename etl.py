import pandas as pd
import sqlite3
import re
import os

# Project Paths
BASE_DIR = '/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/Coding_Practice/projects/nursing_workforce'
DATA_DIR = os.path.join(BASE_DIR, '2022_NSSRN_PUF_ASCII_Package')
SAS_FILE = os.path.join(DATA_DIR, 'nssrn_2022_puf_flat.sas')
TXT_FILE = os.path.join(DATA_DIR, 'nssrn_2022_puf_flat.txt')
DB_FILE = os.path.join(BASE_DIR, 'nursing.db')

def parse_sas_schema(sas_file_path):
    """
    Parses the SAS input statement to get variable names and column specifications.
    Returns: list of tuples (col_name, start_col, end_col) and list of (col_name, width)
    """
    variables = []
    
    with open(sas_file_path, 'r') as f:
        lines = f.readlines()
        
    # Find the data step and input section
    in_input = False
    
    # Regex to span potential multi-line input or flexible whitespace
    # Looking for lines like:  ADDLANG 1-1
    # or  CNTRLNUM $31-40
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
                var_name = match.group(1)
                start_col = int(match.group(2))
                end_col = int(match.group(3))
                variables.append({
                    'name': var_name,
                    'start': start_col,
                    'end': end_col
                })
    
    return variables

def load_data(variables):
    """
    Reads the fixed-width text file using the parsed schema.
    """
    # Calculate widths for pandas read_fwf
    # pandas colspecs takes (start, end) where start is inclusive, end is exclusive (0-based)
    # SAS uses 1-based indexing inclusive
    
    colspecs = []
    names = []
    dtype_map = {}
    
    for var in variables:
        # SAS: 1 to 1 -> Pandas: 0 to 1
        # SAS: 2 to 3 -> Pandas: 1 to 3
        start = var['start'] - 1
        end = var['end']
        colspecs.append((start, end))
        names.append(var['name'])
        
        # We'll read everything as string first to handle 'L', 'M' missing values correctly, 
        # or rely on pandas na_values.
        # But 'CNTRLNUM' should definitely be string. Others can be inferred later or cleaned.
        # Let's try letting pandas infer types but specifying na_values
        
    print(f"Detected {len(variables)} variables.")
    
    # 'L' and 'M' are missing values per SAS script
    missing_values = ['L', 'M', ' ', '.'] 
    
    print("Reading text file... this might take a minute.")
    df = pd.read_fwf(
        TXT_FILE,
        colspecs=colspecs,
        names=names,
        na_values=missing_values,
        chunksize=10000 
    )
    
    conn = sqlite3.connect(DB_FILE)
    
    chunk_num = 0
    for chunk in df:
        chunk_num += 1
        print(f"Processing chunk {chunk_num}...")
        chunk.to_sql('nssrn', conn, if_exists='append' if chunk_num > 1 else 'replace', index=False)
        
    conn.close()
    print("Data loading complete.")

if __name__ == "__main__":
    print("Parsing SAS schema...")
    vars_list = parse_sas_schema(SAS_FILE)
    if not vars_list:
        print("Error: No variables found in SAS file. Check the Regex or file content.")
    else:
        print(f"Found {len(vars_list)} variables. Loading data...")
        load_data(vars_list)
