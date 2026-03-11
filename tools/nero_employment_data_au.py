import os
import zipfile
import tempfile
import logging
import datetime
import sys
import pandas as pd
from curl_cffi import requests

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(repo_root, "data", "log", "nero")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'nero.log')
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_possible_nero_urls(year, month):
    """
    Generates potential NERO zip download URLs for a given year and month.
    """
    folder_date = datetime.date(year, month, 1) + datetime.timedelta(days=32)
    folder_year = folder_date.year
    folder_month = folder_date.month
    
    base_url = f"https://www.jobsandskills.gov.au/sites/default/files/{folder_year}-{folder_month:02d}"
    main_url = f"{base_url}/{year}-{month:02d}_nero.zip"
    regional_url = f"{base_url}/{year}-{month:02d}_nero_for_regional_and_northern_australia.zip"
    
    return [main_url, regional_url]

def convert_extracted_csvs_to_excel(extracted_files):
    for fp in extracted_files:
        if fp.lower().endswith('.csv'):
            logger.info(f"Converting {fp} to Excel...")
            try:
                df = pd.read_csv(fp)
                # Excel has a strict 1,048,576 row limit.
                if len(df) > 1000000 and 'state_name' in df.columns:
                    logger.info(f"File {fp} has {len(df)} rows (>1M). Splitting by state to fit in Excel.")
                    for state in df['state_name'].dropna().unique():
                        state_df = df[df['state_name'] == state]
                        if len(state_df) <= 1000000:
                            out_name = fp.replace('.csv', f'_{state}.xlsx')
                            logger.info(f" -> Saving {state} subset to {out_name} ({len(state_df)} rows)...")
                            state_df.to_excel(out_name, index=False)
                        else:
                            # Chunk it further if a state alone is more than 1M rows
                            chunks = [state_df[i:i+1000000] for i in range(0, len(state_df), 1000000)]
                            for idx, chunk in enumerate(chunks, 1):
                                out_name = fp.replace('.csv', f'_{state}_part{idx}.xlsx')
                                logger.info(f" -> Saving {state} part {idx} to {out_name} ({len(chunk)} rows)...")
                                chunk.to_excel(out_name, index=False)
                else:
                    out_name = fp.replace('.csv', '.xlsx')
                    logger.info(f" -> Saving {out_name} ({len(df)} rows)...")
                    df.to_excel(out_name, index=False)
            except Exception as e:
                logger.error(f"Failed to convert {fp} to Excel: {e}")

def download_and_extract_latest_nero_data(output_dir="data/nero", months_to_check=3):
    """
    Attempts to download the latest NERO data by checking the past few months.
    Uses curl_cffi to perfectly impersonate Chrome TLS fingerprinting to bypass bot protection.
    """
    ensure_dir(output_dir)
    extracted_files = []
    
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    
    found_any = False

    logger.info("Starting curl_cffi session to download NERO data.")
    
    # Create an impersonate session
    session = requests.Session(impersonate="chrome")

    for i in range(months_to_check):
        m = current_month - i
        y = current_year
        while m <= 0:
            m += 12
            y -= 1
        
        urls_to_try = get_possible_nero_urls(y, m)
        
        for url in urls_to_try:
            logger.info(f"Trying to download from {url}...")
            file_name = url.split("/")[-1]
            zip_path = os.path.join(tempfile.gettempdir(), file_name)
            
            try:
                response = session.get(url, timeout=60)
                
                if response.status_code == 200:
                    with open(zip_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Successfully downloaded: {zip_path}")
                    
                    logger.info(f"Extracting {file_name} into {output_dir}")
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(output_dir)
                            extracted_files.extend(
                                [os.path.join(output_dir, name) for name in zip_ref.namelist()]
                            )
                            logger.info(f" -> Extracted contents of {file_name}")
                    except zipfile.BadZipFile:
                        logger.error(f"Downloaded file {zip_path} is not a valid zip archive.")
                    except Exception as e:
                        logger.error(f"Failed to extract {zip_path}. Error: {e}")
                    finally:
                        if os.path.exists(zip_path):
                            try:
                                os.remove(zip_path)
                            except:
                                pass
                            
                    found_any = True
                elif response.status_code == 404:
                    logger.debug(f"File not found (404) at: {url}")
                else:
                    logger.warning(f"Failed to download (Status {response.status_code}) from {url}")
                    
            except Exception as e:
                safe_error_msg = str(e).encode('ascii', 'ignore').decode()
                logger.error(f"Request error for {url}: {safe_error_msg}")
        
        # If we successfully found at least one file for this month, don't check older months
        if found_any:
            break

    if not found_any:
        logger.error(f"Could not find any NERO data for the past {months_to_check} months.")

    logger.info(f"Successfully extracted {len(extracted_files)} files.")
    convert_extracted_csvs_to_excel(extracted_files)
    return extracted_files

if __name__ == "__main__":
    target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "nero")
    download_and_extract_latest_nero_data(target_dir)
