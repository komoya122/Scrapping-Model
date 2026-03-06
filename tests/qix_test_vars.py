import asyncio
import websockets
import json

async def check_vars():
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
        
        list_def = {
            'qInfo': {'qId': 'VariableList', 'qType': 'VariableList'},
            'qVariableListDef': {'qType': 'variable'}
        }
        res = await call('CreateSessionObject', app_handle, [list_def])
        h = res.get('qReturn', {}).get('qHandle')
        
        lay = await call('GetLayout', h)
        items = lay.get('qLayout', {}).get('qVariableList', {}).get('qItems', [])
        
        for i in items:
            name = i.get('qName', '').lower()
            if any(x in name for x in ['occ', 'point', 'state', 'show', 'tog']):
                print(f"Var: {i.get('qName')}")

asyncio.run(check_vars())
