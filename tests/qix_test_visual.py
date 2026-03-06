import time
import urllib.parse
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    url = "https://api.dynamic.reports.employment.gov.au/anonap/single/?appid=aaac76b5-ad30-477e-9ca0-472f8ab57fc8&sheet=1fbfd90f-e36c-44b9-a078-a7c78a46792c"
    print("Navigating to:", url)
    page.goto(url, wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(10000)
    
    page.screenshot(path='data/output/visual_check.png', full_page=True)
    print("Screenshot saved to data/output/visual_check.png")
    
    # Dump body text to see if anything is readable
    text = page.locator('body').inner_text()
    with open('data/output/body_text.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    
    browser.close()
