import os
import logging
import pandas as pd
from bs4 import BeautifulSoup
from curl_cffi import requests
from datetime import datetime

# Setup logging
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(repo_root, "data", "log", "visa_types")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "state_visa_scraper.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_soup(url, session):
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

def scrape_nsw(session):
    # Primary URL with fallback to root if DNS fails
    url = "https://www.nsw.gov.au/visas-and-migration"
    root_url = "https://nsw.gov.au/visas-and-migration"
    
    soup = get_soup(url, session)
    if not soup:
        logging.info("Retrying NSW with root domain...")
        soup = get_soup(root_url, session)
        if soup: url = root_url

    status = "Check website"
    if soup:
        # Looking for common terms in migration status
        text = soup.get_text().lower()
        if "closed" in text and "2025-26" in text:
            status = "Partially Closed (2025-26)"
        elif "open" in text:
            status = "Open"
    return {"State": "NSW", "Program": "Investment NSW", "Link": url, "Status": status, "Visas": "190, 491"}

def scrape_vic(session):
    url = "https://liveinmelbourne.vic.gov.au"
    soup = get_soup(url, session)
    status = "Check website"
    if soup:
        text = soup.get_text().lower()
        if "2025–26" in text and ("allocation" in text or "open" in text):
            status = "Open (2025-26)"
        elif "program is open" in text or "applications are open" in text:
            status = "Open"
    return {"State": "VIC", "Program": "Live in Melbourne", "Link": url, "Status": status, "Visas": "190, 491"}

def scrape_qld(session):
    url = "https://migration.qld.gov.au"
    soup = get_soup(url, session)
    status = "Check website"
    if soup:
        text = soup.get_text().lower()
        if "2025-26" in text and "open" in text:
            status = "Open (2025-26)"
        elif "currently open" in text:
            status = "Open"
    return {"State": "QLD", "Program": "Migration Queensland", "Link": url, "Status": status, "Visas": "190, 491"}

def scrape_wa(session):
    url = "https://migration.wa.gov.au" # Root domain is canonical
    soup = get_soup(url, session)
    status = "Check website"
    if soup:
        text = soup.get_text().lower()
        if "invitation rounds" in text:
            status = "Active"
    return {"State": "WA", "Program": "Migration WA", "Link": url, "Status": status, "Visas": "190, 491"}

def scrape_sa(session):
    url = "https://www.migration.sa.gov.au"
    soup = get_soup(url, session)
    status = "Check website"
    if soup:
        text = soup.get_text().lower()
        if "open" in text:
            status = "Open"
    return {"State": "SA", "Program": "Move to South Australia", "Link": url, "Status": status, "Visas": "190, 491"}

def scrape_tas(session):
    url = "https://www.migration.tas.gov.au"
    soup = get_soup(url, session)
    status = "Check website"
    if soup:
        text = soup.get_text().lower()
        if "paused" in text:
            status = "Invitations Paused"
        elif "open" in text:
            status = "Open"
    return {"State": "TAS", "Program": "Migration Tasmania", "Link": url, "Status": status, "Visas": "190, 491"}

def scrape_nt(session):
    # New domain and specific eligibility path
    url = "https://australiasnorthernterritory.com.au/move/migrate-to-work/nt-government-visa-nomination/eligibility"
    soup = get_soup(url, session)
    status = "Check website"
    if soup:
        text = soup.get_text().lower()
        if "closed to new" in text or "received sufficient applications" in text or "portal has closed" in text:
            status = "Closed to new applications"
        elif "open" in text:
            status = "Open"
    return {"State": "NT", "Program": "The Territory", "Link": url, "Status": status, "Visas": "190, 491"}

def scrape_act(session):
    url = "https://www.act.gov.au/migration"
    soup = get_soup(url, session)
    status = "Protected (Check Manually)" # Default if Cloudflare block (403)
    if soup:
        text = soup.get_text().lower()
        if "invitation rounds" in text:
            status = "Open / Regular Rounds"
    return {"State": "ACT", "Program": "ACT Migration", "Link": url, "Status": status, "Visas": "190, 491"}

def main():
    logging.info("Starting State Visa Program Status Scraper...")
    
    session = requests.Session(impersonate="chrome")
    
    results = []
    
    # Run scrapers
    results.append(scrape_nsw(session))
    results.append(scrape_vic(session))
    results.append(scrape_qld(session))
    results.append(scrape_wa(session))
    results.append(scrape_sa(session))
    results.append(scrape_tas(session))
    results.append(scrape_nt(session))
    results.append(scrape_act(session))
    
    df = pd.DataFrame(results)
    df['Last Checked'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save output
    output_dir = os.path.join(repo_root, "data", "visa_types")
    os.makedirs(output_dir, exist_ok=True)
    
    csv_file = os.path.join(output_dir, "state_visa_status.csv")
    excel_file = os.path.join(output_dir, "state_visa_status.xlsx")
    
    df.to_csv(csv_file, index=False)
    df.to_excel(excel_file, index=False)
    
    logging.info(f"Results saved to {csv_file} and {excel_file}")
    logging.info("Scraping completed.")

if __name__ == "__main__":
    main()
