import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://api.dynamic.reports.employment.gov.au/anonap/single/?appid=aaac76b5-ad30-477e-9ca0-472f8ab57fc8&sheet=799018bf-5805-4685-8f99-2af996e08197", wait_until="domcontentloaded", timeout=60000)
    
    page.wait_for_function("() => (window.require || window.qlik) !== undefined", timeout=60000)
    page.wait_for_timeout(5000)
    
    res = page.evaluate("""() => {
        return {
            has_require: typeof window.require,
            has_qlik: typeof window.qlik,
            require_keys: window.require ? Object.keys(window.require) : []
        };
    }""")
    print("Globals:", res)
    
    try:
        res2 = page.evaluate("""async () => {
            return new Promise((res) => {
                if (window.require) {
                    try {
                        let loadTimer = setTimeout(() => { res('require timeout'); }, 10000);
                        window.require(['js/qlik'], function(qlik){ 
                            clearTimeout(loadTimer);
                            res('qlik type: ' + typeof qlik + ', keys: ' + (qlik ? Object.keys(qlik).join(',') : 'none')); 
                        }, function(err) {
                            clearTimeout(loadTimer);
                            res('require error: ' + err.toString());
                        });
                    } catch(e) {
                        res('require threw: ' + e.toString());
                    }
                } else if (window.qlik) {
                    res('window.qlik exists');
                } else {
                    res('no require or qlik');
                }
            });
        }""")
        print("RequireJS result:", res2)
    except Exception as e:
        print("Error evaluating require:", e)

    browser.close()
