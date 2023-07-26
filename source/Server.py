import os
import asyncio
from dotenv import load_dotenv
from Subscriber import Subscriber
from Pool import Pool
from Handler import Handler
from Strategy import Strategy

async def main():
    """
    Main server to set up pools, connecting to the network and executing the strategy.
    """
    # Load environment variables
    load_dotenv()

    # Set up Pool A and Pool B to update pool reserves and store in memory
    pool_a = Pool("Pool A", os.getenv("RPC_WS_URL"), os.getenv("POOL_A_CONTRACT_ADDRESS"), os.getenv("POOL_A_CONTRACT_ABI"))
    pool_b = Pool("Pool B", os.getenv("RPC_WS_URL"), os.getenv("POOL_B_CONTRACT_ADDRESS"), os.getenv("POOL_B_CONTRACT_ABI"))

    # Define subscriber and handler
    subscriber = Subscriber(os.getenv("RPC_WS_URL"))
    handler = Handler(pool_a, pool_b)

    # Subscribe to the network and execute strategy
    await subscriber.subscribe(handler.handle_new_block_event)

if __name__ == "__main__":
    asyncio.run(main())
