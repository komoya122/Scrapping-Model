"""Selenium-based exporter for SkillSelect EOI

Interactive script that asks for:
- occupation
- point
- nominated_state
- visa type (choose among subclass 189, 190, 491)

The script applies selections via the Qlik JS API in the page context, opens
the results sheet, triggers export and downloads the CSV to `data/output/`.

Requirements:
  pip install selenium requests
  Place `chromedriver.exe` in `drivers/` (or adjust path below).

Run:
  python tools/qlik_selenium_export.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


APPID = "aaac76b5-ad30-477e-9ca0-472f8ab57fc8"
PARAM_SHEET = "799018bf-5805-4685-8f99-2af996e08197"
RESULT_SHEET = "1fbfd90f-e36c-44b9-a078-a7c78a46792c"
BASE_SINGLE = "https://api.dynamic.reports.employment.gov.au/anonap/single/"

# Chromedriver path (adjust if needed)
CHROME_DRIVER = str(Path(__file__).parents[1] / "drivers" / "chromedriver.exe")


def prompt(msg: str) -> Optional[str]:
    v = input(msg).strip()
    return v if v != "" else None


def choose_visa() -> Optional[str]:
    options = ["subclass 189", "subclass 190", "subclass 491"]
    print("Visa type options:")
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    s = input("Choose visa type (1-3) or press Enter to skip: ").strip()
    if not s:
        return None
    try:
        idx = int(s) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    print("Invalid choice, skipping visa type")
    return None


def make_out_path(occupation: Optional[str], point: Optional[str], state: Optional[str], visa: Optional[str]) -> str:
    t = time.strftime("%Y%m%d_%H%M%S")
    occ = occupation or "any"
    pt = point or "any"
    st = state or "any"
    vs = (visa or "any").replace(' ', '_')
    fname = f"eoi_{occ}_{pt}_{st}_{vs}_{t}.csv"
    out = Path("data") / "output" / fname
    out.parent.mkdir(parents=True, exist_ok=True)
    return str(out)


def wait_for_window_var(driver, varname, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        val = driver.execute_script(f"return window.{varname} !== undefined ? window.{varname} : null")
        if val is not None:
            return val
        time.sleep(0.5)
    return None


def run(occupation: Optional[str], point: Optional[str], nominated_state: Optional[str], visa: Optional[str]):
    csv_out = make_out_path(occupation, point, nominated_state, visa)

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")

    # Prefer local chromedriver if present, otherwise try webdriver-manager
    if Path(CHROME_DRIVER).is_file():
        service = Service(CHROME_DRIVER)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        try:
            from webdriver_manager.chrome import ChromeDriverManager
        except Exception:
            raise RuntimeError(f"Chromedriver not found at {CHROME_DRIVER}.\nInstall webdriver-manager (`pip install webdriver-manager`) or place chromedriver.exe in drivers/.")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)

    try:
        # Open parameter sheet
        params_url = f"{BASE_SINGLE}?appid={APPID}&sheet={PARAM_SHEET}"
        print("Opening parameter sheet:", params_url)
        driver.get(params_url)

        # Wait until qlik is available (extended timeout)
        print("Waiting for Qlik API to load...")
        qlik_ready = wait_for_window_var(driver, '_qlik_ready')
        # We'll not rely on that var; instead poll for window.require or window.qlik
        end = time.time() + 60
        while time.time() < end:
            has = driver.execute_script("return (window.require !== undefined) || (window.qlik !== undefined)")
            if has:
                break
            time.sleep(0.5)

        # Inject JS to apply selections
        print("Applying selections via Qlik API (may take a few seconds)...")
        js_apply = """
        (function(appid, occupation, point, state, visa){
            function requireQlik(){
                return new Promise(function(res){
                    if(window.require){
                        window.require(['js/qlik'], function(qlik){ res(qlik); });
                    }else if(window.qlik){
                        res(window.qlik);
                    }else{
                        res(null);
                    }
                });
            }
            requireQlik().then(function(qlik){
                if(!qlik){ window._qlik_sel_result = {error:'qlik_not_found'}; return; }
                var app = qlik.openApp(appid, {});
                app.getList('FieldList', function(reply){
                    var fields = reply.qFieldList.qItems;
                    function findField(cands){
                        cands = cands.map(function(x){ return x.toLowerCase();});
                        for(var i=0;i<fields.length;i++){
                            var name = fields[i].qName.toLowerCase();
                            for(var j=0;j<cands.length;j++){
                                if(name.indexOf(cands[j])!==-1) return fields[i].qName;
                            }
                        }
                        return null;
                    }
                    var occField = findField(['occupation','occupations','occupation groups']);
                    var pointField = findField(['point','points','partner skills score']);
                    var stateField = findField(['nominated state','nominatedstate','state','nominated_state']);
                    var visaField = findField(['visa','visa type','visa_type','subclass']);
                    var applied = [];
                    try{ if(occField && occupation) app.field(occField).selectMatch(occupation, true, false), applied.push({field:occField,val:occupation}); }catch(e){}
                    try{ if(pointField && point) app.field(pointField).selectMatch(point, true, false), applied.push({field:pointField,val:point}); }catch(e){}
                    try{ if(stateField && state) app.field(stateField).selectMatch(state, true, false), applied.push({field:stateField,val:state}); }catch(e){}
                    try{ if(visaField && visa) app.field(visaField).selectMatch(visa, true, false), applied.push({field:visaField,val:visa}); }catch(e){}
                    window._qlik_sel_result = {applied:applied, found:{occField:occField,pointField:pointField,stateField:stateField,visaField:visaField}};
                });
            });
        })(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4]);
        """

        driver.execute_script(js_apply, APPID, occupation, point, nominated_state, visa)

        sel = wait_for_window_var(driver, '_qlik_sel_result', timeout=30)
        print('Selection result:', sel)

        # If Qlik wasn't found in the page, save debug artifacts to help diagnose
        if isinstance(sel, dict) and sel.get('error') == 'qlik_not_found':
            ts = time.strftime("%Y%m%d_%H%M%S")
            dump_dir = Path('data') / 'output'
            dump_dir.mkdir(parents=True, exist_ok=True)
            png = dump_dir / f"qlik_debug_{ts}.png"
            html = dump_dir / f"qlik_debug_{ts}.html"
            try:
                driver.save_screenshot(str(png))
                open(str(html), 'w', encoding='utf-8').write(driver.page_source)
                print('Saved debug screenshot and HTML to', png, html)
                print('Tip: try running without headless mode to interactively inspect the page (remove `--headless=new`).')
            except Exception as e:
                print('Failed to save debug artifacts:', e)

        # Navigate to results sheet
        results_url = f"{BASE_SINGLE}?appid={APPID}&sheet={RESULT_SHEET}"
        print('Opening results sheet:', results_url)
        driver.get(results_url)

        # Wait for Qlik
        end = time.time() + 30
        while time.time() < end:
            has = driver.execute_script("return (window.require !== undefined) || (window.qlik !== undefined)")
            if has:
                break
            time.sleep(0.5)

        # List objects and find table id
        print('Retrieving object list...')
        driver.execute_script(
            """
            (function(appid){
                function requireQlik(){
                    return new Promise(function(res){
                        if(window.require){ window.require(['js/qlik'], function(qlik){ res(qlik); }); }
                        else if(window.qlik){ res(window.qlik); }
                        else{ res(null); }
                    });
                }
                requireQlik().then(function(qlik){
                    var app = qlik.openApp(appid, {});
                    app.getObjectList(function(reply){
                        var list = reply.qAppObjectList.qItems.map(function(i){ return {id:i.qInfo.qId, title: (i.qMeta&&i.qMeta.title)?i.qMeta.title:'', type: (i.qData&&i.qData.visualization)?i.qData.visualization:''}; });
                        window._qlik_obj_list = list;
                    });
                });
            })(arguments[0]);
            """,
            APPID,
        )

        objs = wait_for_window_var(driver, '_qlik_obj_list', timeout=20)
        print('Found objects count:', len(objs) if objs else 0)

        table_id = None
        if objs:
            for o in objs:
                t = (o.get('type') or '').lower()
                title = (o.get('title') or '').lower()
                if 'table' in t or 'table' in title or 'result' in title:
                    table_id = o.get('id')
                    break
            if not table_id:
                table_id = objs[0].get('id')

        if not table_id:
            print('No table object found; aborting')
            return

        print('Using object id:', table_id)

        # Trigger export
        driver.execute_script(
            """
            (function(appid, objid){
                function requireQlik(){
                    return new Promise(function(res){
                        if(window.require){ window.require(['js/qlik'], function(qlik){ res(qlik); }); }
                        else if(window.qlik){ res(window.qlik); }
                        else{ res(null); }
                    });
                }
                requireQlik().then(function(qlik){
                    var app = qlik.openApp(appid, {});
                    app.getObject(objid).then(function(model){
                        var table = new qlik.table(model);
                        table.exportData({download:false}, function(link){ window._qlik_export_link = link; });
                    }).catch(function(e){ window._qlik_export_error = e && e.toString(); });
                });
            })(arguments[0], arguments[1]);
            """,
            APPID,
            table_id,
        )

        export_link = wait_for_window_var(driver, '_qlik_export_link', timeout=30)
        if not export_link:
            err = driver.execute_script('return window._qlik_export_error || null')
            print('Export failed:', err)
            return

        if isinstance(export_link, str) and export_link.startswith('/'):
            full = 'https://api.dynamic.reports.employment.gov.au' + export_link
        else:
            full = export_link

        print('Downloading CSV from', full)
        r = requests.get(full, timeout=60)
        r.raise_for_status()
        open(csv_out, 'wb').write(r.content)
        print('Saved CSV to', csv_out)

    finally:
        driver.quit()


if __name__ == '__main__':
    occ = prompt('Occupation (code or name): ')
    pt = prompt('Point (optional): ')
    st = prompt('Nominated state (optional): ')
    visa = choose_visa()
    run(occ, pt, st, visa)
