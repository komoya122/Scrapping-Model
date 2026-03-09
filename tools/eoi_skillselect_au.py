"""Engine API-based exporter for SkillSelect EOI

Requirements:
  pip install websockets requests

Usage:
  python tools/eoi_skillselect_au.py

The script connects to the Qlik Sense Engine API via WebSockets. It will
auto-select the latest "As At Month", apply the requested selections,
and download the results table.
"""
import sys
import subprocess

try:
    import websockets
except ImportError:
    print("Installing required package 'websockets'...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Optional
import requests

log_dir = Path("data") / "log" / "eoi_ss"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "eoi_ss.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

APPID = "aaac76b5-ad30-477e-9ca0-472f8ab57fc8"
TABLE_ID = "eymDb"
WS_URL = f"wss://api.dynamic.reports.employment.gov.au/anonap/app/{APPID}"
BASE_URL = "https://api.dynamic.reports.employment.gov.au"

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
    except ValueError: pass
    print("Invalid choice, skipping visa type")
    return None

def make_out_path(as_at_month: str, occupation: Optional[str]) -> str:
    # Use YYYYMMDD for the date format
    t = time.strftime("%Y%m%d")
    
    # Clean up month string (e.g. from "02/2026" to "02-2026") to be filesystem safe
    month_clean = as_at_month.replace("/", "-").replace("\\", "-")
    
    # Clean up occupation string
    occ = (occupation or "All").replace("/", "-").replace("\\", "-").replace(" ", "_")
    
    fname = f"eoi_{month_clean}_{occ}_{t}.csv"
    out = Path("data") / "eoi_ss" / fname
    out.parent.mkdir(parents=True, exist_ok=True)
    return str(out)

async def get_available_months() -> list[str]:
    logging.info("Fetching available 'As At Month' options from Qlik...")
    months = []
    
    session = requests.Session()
    session.get(f"{BASE_URL}/anonap/single/?appid={APPID}", timeout=10)
    cookies = session.cookies.get_dict()
    headers = {"Cookie": "; ".join([f"{k}={v}" for k, v in cookies.items()])}
    
    async with websockets.connect(WS_URL, subprotocols=["qlik-qix-session-v1"], additional_headers=headers) as ws:
        msg_id = 1
        async def call(method, handle, params=None):
            nonlocal msg_id
            m_id = msg_id
            msg_id += 1
            await ws.send(json.dumps({'jsonrpc': '2.0', 'id': m_id, 'method': method, 'handle': handle, 'params': params or []}))
            while True:
                res = await ws.recv()
                data = json.loads(res)
                if data.get('id') == m_id:
                    return data.get('result', {})

        await call('OpenDoc', -1, [APPID])
        
        list_def_m = {
            "qInfo": {"qId": "tmp_m", "qType": "ListObject"},
            "qListObjectDef": {"qDef": {"qFieldDefs": ["As At Month"], "qSortCriterias": [{"qSortByNumeric": -1}]}, 
            "qInitialDataFetch": [{"qTop":0, "qLeft":0, "qWidth":1, "qHeight":100}]}
        }
        res_m = await call("CreateSessionObject", 1, [list_def_m])
        mh = res_m.get("qReturn", {}).get("qHandle")
        if mh:
            lay_m = await call("GetLayout", mh)
            matrix = lay_m.get("qLayout", {}).get("qListObject", {}).get("qDataPages", [])[0].get("qMatrix", [])
            for row in matrix:
                text = row[0].get("qText")
                if text:
                    months.append(text)
    return months


async def qix_export(occupation, point, nominated_state, visa, target_months):
    logging.info("Connecting to QIX Engine API...")
    
    # Needs a session to store Qlik Proxy Cookies so the final TempContent download is authorized
    session = requests.Session()
    session.get(f"{BASE_URL}/anonap/single/?appid={APPID}", timeout=10)
    cookies = session.cookies.get_dict()
    headers = {"Cookie": "; ".join([f"{k}={v}" for k, v in cookies.items()])}
    
    msg_id = 1
    # Note: older websockets uses extra_headers, newer uses additional_headers.
    # websockets 14+ natively supports additional_headers.
    # We set ping_interval=None because the Qlik Engine might block for >20 seconds while generating large CSVs.
    async with websockets.connect(
        WS_URL, 
        subprotocols=["qlik-qix-session-v1"], 
        max_size=10**8, 
        additional_headers=headers,
        ping_interval=None
    ) as ws:
        async def call(method, handle, params=None):
            nonlocal msg_id
            m_id = msg_id
            msg_id += 1
            await ws.send(json.dumps({
                "jsonrpc": "2.0", "id": m_id, "method": method, "handle": handle, "params": params or []
            }))
            while True:
                res = await ws.recv()
                data = json.loads(res)
                if data.get("id") == m_id:
                    if "error" in data:
                        raise RuntimeError(f"API Error ({method}): {data['error'].get('message', data['error'])}")
                    return data.get("result", {})
                    
        # 1. Open Document
        res = await call("OpenDoc", -1, [APPID])
        app_handle = res.get("qReturn", {}).get("qHandle")
        
        # Helper to select a value
        async def apply_sel(field_name, value):
            if not value: return
            logging.info(f"Applying selection: {field_name} = '{value}'")
            list_def = {"qInfo": {"qId": f"tmp_{field_name}", "qType": "ListObject"},"qListObjectDef": {"qDef": {"qFieldDefs": [field_name]}, "qInitialDataFetch": []}}
            lobj = await call("CreateSessionObject", app_handle, [list_def])
            h = lobj.get("qReturn", {}).get("qHandle")
            await call("SearchListObjectFor", h, ["/qListObjectDef", value])
            await call("AcceptListObjectSearch", h, ["/qListObjectDef", True])

        # Mandatory Filter: As At Month
        # We fetch the top result and select it implicitly because the new dashboard logic requires it.
        list_def_m = {
            "qInfo": {"qId": "tmp_m", "qType": "ListObject"},
            "qListObjectDef": {"qDef": {"qFieldDefs": ["As At Month"], "qSortCriterias": [{"qSortByNumeric": -1}]}, 
            "qInitialDataFetch": [{"qTop":0, "qLeft":0, "qWidth":1, "qHeight":100}]}
        }
        res_m = await call("CreateSessionObject", app_handle, [list_def_m])
        mh = res_m.get("qReturn", {}).get("qHandle")
        lay_m = await call("GetLayout", mh)
        matrix = lay_m.get("qLayout", {}).get("qListObject", {}).get("qDataPages", [])[0].get("qMatrix", [])
        
        month_map = {}
        if matrix:
            for row in matrix:
                text = row[0].get("qText")
                elem = row[0].get("qElemNumber")
                if text is not None and elem is not None:
                    month_map[text] = elem

        # Apply persistent User Selections FIRST
        await apply_sel("Occupation", occupation)
        await apply_sel("Point", point)
        await apply_sel("Nominated State", nominated_state)
        await apply_sel("Visa Type", visa)

        # Identify the Main Table and strip definition limits
        logging.info("Fetching results table definition...")
        t_res = await call("GetObject", app_handle, ["eymDb"])
        t_h = t_res.get("qReturn", {}).get("qHandle")
        props_res = await call("GetProperties", t_h)
        qProp = props_res.get("qProp", {})
        
        hc = qProp.get("qHyperCubeDef", {})
        
        # Dimensions 0=Month, 2=Visa, 4=Occupation, 5=EOI Status, 6=Points, 12=State
        target_indices = [0, 2, 4, 5, 6, 12]
        all_dims = hc.get("qDimensions", [])
        
        selected_dims = []
        for i in target_indices:
            if i < len(all_dims):
                d = dict(all_dims[i])
                if "qCalcCondition" in d:
                    del d["qCalcCondition"]
                selected_dims.append(d)
                
        custom_hc = dict(hc)
        custom_hc["qDimensions"] = selected_dims
        if "qCalcCondition" in custom_hc:
            del custom_hc["qCalcCondition"]
            
        logging.info("Creating custom unrestricted Session Table...")
        session_obj_def = {
            "qInfo": {"qId": "CustomUnrestrictedTable", "qType": "table"},
            "qHyperCubeDef": custom_hc
        }
        cust_res = await call("CreateSessionObject", app_handle, [session_obj_def])
        cust_h = cust_res.get("qReturn", {}).get("qHandle")
        
        # Decide the filename prefix based on single or multi-month
        month_prefix = "All-Months" if len(target_months) > 1 else target_months[0]
        csv_out = make_out_path(month_prefix, occupation)
        
        # To avoid duplicating headers in a multi-month merge
        is_first_write = True
        
        # Iterate over all requested months using the Qlik associative associative model
        for m_text in target_months:
            elem_id = month_map.get(m_text)
            if elem_id is None: 
                logging.warning(f"Month {m_text} not found in Engine, skipping.")
                continue
                
            logging.info(f"--- Extracting Data for Month: {m_text} ---")
            await call("SelectListObjectValues", mh, ["/qListObjectDef", [elem_id], False])
            
            # Because Qlik is reactive, selecting the month automatically updates `CustomUnrestrictedTable`!
            lay = await call("GetLayout", cust_h)
            cust_hc_lay = lay.get("qLayout", {}).get("qHyperCube", {})
            qcy = cust_hc_lay.get("qSize", {}).get("qcy", 0)
            
            if qcy == 0:
                logging.info(f"No data for {m_text}. Skipping...")
                continue
                
            logging.info(f"Compiling {qcy} combined rows...")
            exp = await call("ExportData", cust_h, ["CSV_C", "/qHyperCubeDef", "Export.csv", "A"])
            download_uri = exp.get("qUrl")
            
            if not download_uri:
                logging.error(f"Failed to get export URL for {m_text}.")
                continue
    
            if not download_uri.startswith("/anonap/"):
                download_uri = "/anonap" + download_uri
                
            download_url = BASE_URL + download_uri
            logging.info("Downloading CSV payload...")
            r = session.get(download_url, timeout=60)
            r.raise_for_status()
            
            payload_lines = r.content.splitlines()
            if not payload_lines:
                continue
                
            # If it's not the first file, strip out the header line before appending
            if not is_first_write:
                payload_lines = payload_lines[1:]
                
            with open(csv_out, "ab") as f:
                for line in payload_lines:
                    f.write(line + b"\n")
            
            is_first_write = False
            
        logging.info(f"Success! All selected months merged and saved to {csv_out}")

def run(occupation: Optional[str], point: Optional[str], nominated_state: Optional[str], visa: Optional[str], target_months: list[str]):
    asyncio.run(qix_export(occupation, point, nominated_state, visa, target_months))

if __name__ == '__main__':
    occ = prompt('Occupation (code or name): ')
    pt = prompt('Point (optional): ')
    st = prompt('Nominated state (optional): ')
    visa = choose_visa()
    
    # NEW: Fetch available months via HTTP and query user
    import sys
    months = asyncio.run(get_available_months())
    
    selected_months = []
    if not months:
        print("Failed to fetch available months from Qlik. Aborting.")
        sys.exit(1)
        
    print("\nAvailable 'As At Month' options:")
    print("  0. All Months (Download and Merge Everything)")
    for i, m in enumerate(months, 1):
        print(f"  {i}. {m}")
        
    s = input(f"\nChoose a month (0-{len(months)}) or press Enter for All: ").strip()
    if not s or s == "0":
        selected_months = months
        print("Selected: All Months")
    else:
        try:
            idx = int(s) - 1
            if 0 <= idx < len(months):
                selected_months = [months[idx]]
                print("Selected:", selected_months[0])
            else:
                selected_months = months
                print("Invalid choice, defaulting to All Months")
        except ValueError:
            selected_months = months
            print("Invalid input, defaulting to All Months")
            
    asyncio.run(qix_export(occ, pt, st, visa, selected_months))
