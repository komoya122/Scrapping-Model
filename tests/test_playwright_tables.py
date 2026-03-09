from playwright.sync_api import sync_playwright
import re

def check_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        print("Navigating to National Planning Levels...")
        page.goto('https://immi.homeaffairs.gov.au/what-we-do/migration-program-planning-levels', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        
        # Output the innerText of the parent container to see the shape of the data
        text = page.locator('body').inner_text()
        with open("national_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        print("Scraping State allocations...")
        page.goto('https://immi.homeaffairs.gov.au/what-we-do/state-and-territory-nomination-allocations', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        
        text = page.locator('body').inner_text()
        with open("state_text.txt", "w", encoding="utf-8") as f:
            f.write(text)

        browser.close()

if __name__ == "__main__":
    check_html()
