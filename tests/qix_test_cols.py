import asyncio
import websockets
import json

async def dump_hc():
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
                    return data.get('result', {})
        
        await call('OpenDoc', -1, [app_id])
        
        t_id = "eymDb"
        t_res = await call("GetObject", 1, [t_id])
        t_h = t_res.get("qReturn", {}).get("qHandle")
        props_res = await call("GetProperties", t_h)
        hc = props_res.get("qProp", {}).get("qHyperCubeDef", {})
        
        with open("data/output/hc_raw.json", "w") as f:
            json.dump(hc, f, indent=2)

asyncio.run(dump_hc())
