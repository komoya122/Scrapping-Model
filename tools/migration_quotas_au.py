import os
import json
import logging
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup
from curl_cffi import requests

# Configure logging
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
log_dir = os.path.join(repo_root, "data", "log", "migration_quota")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "migration_quotas.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def scrape_national_quotas(output_dir):
    """
    Scrapes the National Migration Program Planning Levels.
    The data on this page is embedded deeply in a hidden JSON field.
    """
    url = "https://immi.homeaffairs.gov.au/what-we-do/migration-program-planning-levels"
    logging.info(f"Downloading National quotas from {url}...")
    
    try:
        session = requests.Session(impersonate="chrome")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        hidden_input = soup.find('input', id='ctl00_PlaceHolderMain_PageSchemaHiddenField_Input')
        
        if hidden_input and 'value' in hidden_input.attrs:
            val = hidden_input['value']
            data = json.loads(val)
            
            # The HTML is inside the 'block' of the content components
            full_html = ""
            for item in data.get('content', []):
                full_html += item.get('block', '')
                
            tables = pd.read_html(StringIO(full_html))
            if not tables:
                logging.warning("No tables found in the extracted National HTML.")
                return False
                
            # Assume the first extracted table is the primary quota table
            df = tables[0]
            
            # Clean up the dataframe (optional based on format, but saving raw is good first step)
            output_file = os.path.join(output_dir, "national_migration_quotas.csv")
            df.to_csv(output_file, index=False)
            logging.info(f"Successfully saved National quotas to {output_file}")
            return True
        else:
            logging.error("Could not find the hidden JSON data field on the National page.")
            return False
            
    except Exception as e:
        msg = str(e).encode('ascii', 'replace').decode('ascii')
        logging.error(f"Error scraping National quotas: {msg}")
        return False

def scrape_state_allocations(output_dir):
    """
    Scrapes the State and Territory Nomination Allocations.
    The data on this page is in a standard HTML table in the initial source.
    """
    url = "https://immi.homeaffairs.gov.au/what-we-do/state-and-territory-nomination-allocations"
    logging.info(f"Downloading State allocations from {url}...")
    
    try:
        session = requests.Session(impersonate="chrome")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        # We can read the HTML directly using pandas
        tables = pd.read_html(StringIO(response.text))
        if not tables:
            logging.warning("No tables found in the extracted State HTML.")
            return False
            
        # The main allocation table should be the first one
        df = tables[0]
        
        output_file = os.path.join(output_dir, "state_nomination_allocations.csv")
        df.to_csv(output_file, index=False)
        logging.info(f"Successfully saved State allocations to {output_file}")
        return True
        
    except Exception as e:
        msg = str(e).encode('ascii', 'replace').decode('ascii')
        logging.error(f"Error scraping State allocations: {msg}")
        return False

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(repo_root, "data", "migration_quota")
    os.makedirs(output_dir, exist_ok=True)
    
    logging.info("Starting Migration Quota Scraper...")
    national_success = scrape_national_quotas(output_dir)
    state_success = scrape_state_allocations(output_dir)
    
    if national_success and state_success:
        logging.info("Both scraping tasks completed successfully.")
    else:
        logging.warning("One or more scraping tasks failed. Check logs for details.")

if __name__ == "__main__":
    main()
