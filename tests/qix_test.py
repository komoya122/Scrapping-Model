import asyncio
import json
import websockets

async def fetch_month_and_data():
    app_id = "aaac76b5-ad30-477e-9ca0-472f8ab57fc8"
    url = f"wss://api.dynamic.reports.employment.gov.au/anonap/app/{app_id}"
    msg_id = 1
    
    async with websockets.connect(url, subprotocols=["qlik-qix-session-v1"], max_size=10**8) as ws:
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
                        print(f"Error calling {method}: {data['error']}")
                        return None
                    return data.get("result", {})
                    
        await call("OpenDoc", -1, [app_id])
        app_handle = 1
        
        # Select Visa Type
        list_def = {"qInfo": {"qId": "tmp_v", "qType": "ListObject"},"qListObjectDef": {"qDef": {"qFieldDefs": ["Visa Type"]}, "qInitialDataFetch": []}}
        res = await call("CreateSessionObject", app_handle, [list_def])
        h = res.get("qReturn", {}).get("qHandle")
        await call("SearchListObjectFor", h, ["/qListObjectDef", "subclass 189"])
        await call("AcceptListObjectSearch", h, ["/qListObjectDef", True])
        
        # Autoselect As At Month
        list_def_m = {
            "qInfo": {"qId": "tmp_m", "qType": "ListObject"},
            "qListObjectDef": {
                "qDef": {
                    "qFieldDefs": ["As At Month"],
                    "qSortCriterias": [{"qSortByNumeric": -1, "qSortByAscii": -1}]
                }, 
                "qInitialDataFetch": [{"qTop":0, "qLeft":0, "qWidth":1, "qHeight":10}]
            }
        }
        res_m = await call("CreateSessionObject", app_handle, [list_def_m])
        mh = res_m.get("qReturn", {}).get("qHandle")
        lay_m = await call("GetLayout", mh)
        matrix = lay_m.get("qLayout", {}).get("qListObject", {}).get("qDataPages", [])[0].get("qMatrix", [])
        months = [row[0].get("qText") for row in matrix if row[0].get("qText")]
        print("Available months:", months)
        
        if months:
            top_month = months[0]
            print("Auto-selecting latest month:", top_month)
            # Select EXACT match using SelectListObjectValues (since we know the exact text)
            elem_id = matrix[0][0].get("qElemNumber")
            await call("SelectListObjectValues", mh, ["/qListObjectDef", [elem_id], False])
            
        t_id = "eymDb"
        t_res = await call("GetObject", app_handle, [t_id])
        t_h = t_res.get("qReturn", {}).get("qHandle")
        
        lay = await call("GetLayout", t_h)
        hc = lay.get("qLayout", {}).get("qHyperCube", {})
        qcy = hc.get("qSize", {}).get("qcy", 0)
        print(f"Table rows after month selection: {qcy}")
        
        if qcy > 0:
            export_res = await call("ExportData", t_h, ["CSV_C", "/qHyperCubeDef", "Test.csv", "A"])
            print("Export Link:", export_res.get("qUrl"))

asyncio.run(fetch_month_and_data())
