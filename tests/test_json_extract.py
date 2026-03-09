from bs4 import BeautifulSoup
import json
import pandas as pd
from io import StringIO

def extract_tables():
    with open("national_curl.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    hidden_input = soup.find('input', id='ctl00_PlaceHolderMain_PageSchemaHiddenField_Input')
    
    if hidden_input and 'value' in hidden_input.attrs:
        val = hidden_input['value']
        # val is JSON
        data = json.loads(val)
        
        # The HTML is inside the 'block' of the content components
        full_html = ""
        for item in data.get('content', []):
            full_html += item.get('block', '')
            
        print("Successfully extracted hidden HTML.")
        
        try:
            tables = pd.read_html(StringIO(full_html))
            print(f"Found {len(tables)} tables!")
            for i, tbl in enumerate(tables):
                print(f"--- Table {i} ---")
                print(tbl)
                tbl.to_csv("national_quota_test.csv", index=False)
        except Exception as e:
            print("Failed to parse tables:", e)
    else:
        print("Hidden input not found.")

if __name__ == "__main__":
    extract_tables()
