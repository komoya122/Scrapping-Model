import asyncio
import websockets
import json

async def bypass_limit():
    app_id = 'aaac76b5-ad30-477e-9ca0-472f8ab57fc8'
    url = f'wss://api.dynamic.reports.employment.gov.au/anonap/app/{app_id}'
    
    async with websockets.connect(url, subprotocols=['qlik-qix-session-v1'], max_size=10**8) as ws:
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
                    if 'error' in data:
                        return {'error': data['error']}
                    return data.get('result', {})
        
        await call('OpenDoc', -1, [app_id])
        app_handle = 1
        
        # 1. Select Month
        list_def_m = {
            "qInfo": {"qId": "tmp_m", "qType": "ListObject"},
            "qListObjectDef": {"qDef": {"qFieldDefs": ["As At Month"], "qSortCriterias": [{"qSortByNumeric": -1}]}, 
            "qInitialDataFetch": [{"qTop":0, "qLeft":0, "qWidth":1, "qHeight":5}]}
        }
        res_m = await call("CreateSessionObject", app_handle, [list_def_m])
        mh = res_m.get("qReturn", {}).get("qHandle")
        lay_m = await call("GetLayout", mh)
        matrix = lay_m.get("qLayout", {}).get("qListObject", {}).get("qDataPages", [])[0].get("qMatrix", [])
        if matrix:
            elem_id = matrix[0][0].get("qElemNumber")
            await call("SelectListObjectValues", mh, ["/qListObjectDef", [elem_id], False])
            
        # 2. Extract eymDb properties
        t_res = await call("GetObject", app_handle, ["eymDb"])
        t_h = t_res.get("qReturn", {}).get("qHandle")
        props_res = await call("GetProperties", t_h)
        qProp = props_res.get("qProp", {})
        
        hc = qProp.get("qHyperCubeDef", {})
        
        # Indices to keep: 0(Month), 2(Visa Type), 4(Occupation), 5(EOI Status), 6(Points), 12(Nominated State)
        target_indices = [0, 2, 4, 5, 6, 12]
        all_dims = hc.get("qDimensions", [])
        
        selected_dims = []
        for i in target_indices:
            try:
                d = dict(all_dims[i])
                # Remove qCalcCondition
                if "qCalcCondition" in d:
                    del d["qCalcCondition"]
                selected_dims.append(d)
            except IndexError:
                print("Missing index", i)
                
        # Rebuild hc
        custom_hc = dict(hc)
        custom_hc["qDimensions"] = selected_dims
        if "qCalcCondition" in custom_hc:
            del custom_hc["qCalcCondition"]
            
        # Create Session Object
        session_obj_def = {
            "qInfo": {"qId": "CustomTable", "qType": "table"},
            "qHyperCubeDef": custom_hc
        }
        
        print("Creating custom session table...")
        cust_res = await call("CreateSessionObject", app_handle, [session_obj_def])
        cust_h = cust_res.get("qReturn", {}).get("qHandle")
        
        lay = await call("GetLayout", cust_h)
        cust_hc = lay.get('qLayout', {}).get('qHyperCube', {})
        qcx = cust_hc.get('qSize', {}).get('qcx', 0)
        qcy = cust_hc.get('qSize', {}).get('qcy', 0)
        print(f"Custom Cols: {qcx}, Rows: {qcy}")
        
        if qcy > 0:
            exp = await call("ExportData", cust_h, ["CSV_C", "/qHyperCubeDef", "CustomExport.csv", "A"])
            print("Successfully exported custom merged table:", exp.get("qUrl"))

asyncio.run(bypass_limit())
