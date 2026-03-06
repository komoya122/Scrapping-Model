import asyncio
import websockets
import json

async def test_vars():
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
        
        # Select Month to populate table
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
            
        async def set_var(name, val):
            v_res = await call('GetVariableByName', app_handle, [name])
            v_h = v_res.get('qReturn', {}).get('qHandle')
            if v_h:
                await call('SetStringValue', v_h, [val])
                print(f"Set {name} to {val}")
            
        await set_var('vShowOccupations', 'Y')
        await set_var('vShowPoints', 'Y')
        await set_var('vShowEOINomState', 'Y')
        
        # Now get table layout
        t_id = "eymDb"
        t_res = await call("GetObject", app_handle, [t_id])
        t_h = t_res.get("qReturn", {}).get("qHandle")
        
        lay = await call("GetLayout", t_h)
        hc = lay.get('qLayout', {}).get('qHyperCube', {})
        calc = hc.get('qCalcCond', {})
        
        qcx = hc.get('qSize', {}).get('qcx', 0)
        qcy = hc.get('qSize', {}).get('qcy', 0)
        print(f"Cols: {qcx}, Rows: {qcy}")
        
        if qcx == 0 and qcy == 0:
            print("Table disabled by CalcCond.")
        else:
            print("Table rendered successfully with all dimensions enabled!")
            
asyncio.run(test_vars())
