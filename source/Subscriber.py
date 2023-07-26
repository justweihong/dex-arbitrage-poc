import asyncio
from websockets import connect
import json

class Subscriber:
    """
    Serves to interact with the network which the Liquidity Pools (LP) are deployed in, such as subscribing with new blocks.
    """

    def __init__(self, rpc_ws_url: str):
        self.rpc_ws_url = rpc_ws_url

    async def subscribe(self, callback):
        """
        Continuously subscribe to new block events
        """
        async with connect(self.rpc_ws_url) as ws:
            # Start subscription for new blocks
            rpc_new_block_query = '{"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["newHeads"]}'
            await ws.send(rpc_new_block_query)

            while True:
                try:
                    # Receive new block event and send callback
                    message = await asyncio.wait_for(ws.recv(), timeout=15)
                    response = json.loads(message)
                    new_block_data = response["params"]["result"]
                    new_block_no = int(new_block_data["number"], base=16)
                    print(f"INFO: New block mined -  {new_block_no}")
                    callback(new_block_data)
                    
                except Exception as e:
                    # print(str(e))
                    pass