import asyncio
import websockets
import json

async def check_dims():
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
        
        t_id = "eymDb"
        t_res = await call("GetObject", app_handle, [t_id])
        t_h = t_res.get("qReturn", {}).get("qHandle")
        
        props = await call("GetProperties", t_h)
        hc = props.get("qProp", {}).get("qHyperCubeDef", {})
        
        dims = hc.get("qDimensions", [])
        print(f"Total Dims: {len(dims)}")
        for i, d in enumerate(dims):
            dDef = d.get('qDef', {})
            labels = dDef.get('qFieldLabels', [])
            defs = dDef.get('qFieldDefs', [])
            title = labels[0] if labels else (defs[0] if defs else "Unknown")
            calc = d.get('qCalcCondition', {})
            print(f"Dim {i}: {title} | Cond: {calc}")
            
        # Get Master Measure if any
        meas = hc.get("qMeasures", [])
        print(f"Total Meas: {len(meas)}")
        for i, m in enumerate(meas):
            mDef = m.get('qDef', {})
            label = mDef.get('qLabel', '')
            calc = m.get('qCalcCondition', {})
            print(f"Meas {i}: {label} | Cond: {calc}")

asyncio.run(check_dims())
