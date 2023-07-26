import concurrent.futures
from Pool import Pool
from Strategy import Strategy

class Handler:
    """
    Serves to handle events that are being published, such as a new block event.
    """
    def __init__(self, pool_a: Pool, pool_b: Pool):
        self.pool_a = pool_a
        self.pool_b = pool_b

    def handle_new_block_event(self, new_block_data: dict):
        """
        Handles a new block events by updating the pool reserves and executing the arbitrage strategy.
        """
        # Update pools
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

            # Update both pools in parallel
            update_pool_a_task = executor.submit(self.pool_a.update_reserves)
            update_pool_b_task = executor.submit(self.pool_b.update_reserves)
            concurrent.futures.wait([update_pool_a_task, update_pool_b_task])

            # Execute arbitrage strategy
            is_profitable, optimal_amount_ETH = Strategy.execute(self.pool_a, self.pool_b)
        