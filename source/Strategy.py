import os
import requests
import json
import concurrent.futures
from Pool import Pool
from scipy.optimize import minimize_scalar

class Strategy:
    """
    Serves to execute the DEX price arbitrage strategy.
    """
    
    @staticmethod
    def get_optimal_amount_ETH(pool_a: Pool, pool_b: Pool):
        """
        Helper method for execute():
        Get the max ETH to earn based on the price difference between pools.
        """
        # Get pool reserves
        pool_a_reserve_DAI, pool_a_reserve_ETH = pool_a.get_reserves()
        pool_b_reserve_DAI, pool_b_reserve_ETH = pool_b.get_reserves()

        # Get the price of ETH in DAI for both pools
        pool_a_token_ETH_price = pool_a_reserve_DAI/pool_a_reserve_ETH
        pool_b_token_ETH_price = pool_b_reserve_DAI/pool_b_reserve_ETH

        # Determine the pool with lower price (to buy from) and higher price (to sell from)
        if pool_a_token_ETH_price > pool_b_token_ETH_price:
            low_pool_reserve_DAI, low_pool_reserve_ETH = pool_b_reserve_DAI, pool_b_reserve_ETH
            high_pool_reserve_DAI, high_pool_reserve_ETH = pool_a_reserve_DAI, pool_a_reserve_ETH
        else:
            low_pool_reserve_DAI, low_pool_reserve_ETH = pool_a_reserve_DAI, pool_a_reserve_ETH
            high_pool_reserve_DAI, high_pool_reserve_ETH = pool_b_reserve_DAI, pool_b_reserve_ETH


        # Get the negative of the optimal amount of token ETH to provide to get the max amount of token ETH
        def get_negative_amount_ETH_earned(amount_ETH):
            # First Swap: Swap ETH for DAI from high pool (in: ETH, out: DAI)
            amount_ETH_with_fee = 0.997*amount_ETH*pow(10,18)
            amount_DAI_out = ((amount_ETH_with_fee*high_pool_reserve_DAI)/(high_pool_reserve_ETH + amount_ETH_with_fee))/pow(10,18)

            # Second Swap: Swap DAI for ETH from the low pool (in: DAI, out: ETH)
            amount_DAI_with_fee = 0.997*amount_DAI_out*pow(10,18)
            amount_ETH_out = ((amount_DAI_with_fee*low_pool_reserve_ETH)/(low_pool_reserve_DAI + amount_DAI_with_fee))/pow(10,18)

            # Return the amount 1 gained
            amount_ETH_earned = amount_ETH_out - amount_ETH
            return -amount_ETH_earned
        
        try:
            optimize_result = minimize_scalar(get_negative_amount_ETH_earned)
            optimal_amount_ETH, amount_ETH_earned = optimize_result.x, -optimize_result.fun
            # Return optimal amount and amount earned if they are >0
            if optimal_amount_ETH > 0 and amount_ETH_earned > 0:
                return optimal_amount_ETH, amount_ETH_earned 
            else:
                return 0, 0
        except Exception as e: 
            print(f"INFO: No turning points found, no profitable amount - {e}.")
            return 0, 0
    
    @staticmethod
    def get_fast_gas_price():
        """
        Helper method for execute():
        Get the fast gas price (in Gwei) estimate minimize time taken for the arbitrage txn to be mined.
        """
        api_key = os.getenv("ETHERSCAN_API_KEY")
        endpoint = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={api_key}"
        response = requests.get(endpoint)
        fasGasPrice = json.loads(response.content)['result']['FastGasPrice']
        return float(fasGasPrice)
    
    #! Not implemented yet due to time constraints
    @staticmethod
    def get_gas_used():
        """
        Helper method for execute():
        Calculate gas used for contract to execute the arbitrage execution in the network.
        """
        # After solidity contract containing arbitrage method gets deployed, use Web3.py's `estimate_gas()` method to estimate
        return 50000
    
    @staticmethod
    def execute(pool_a: Pool, pool_b: Pool):
        """
        Main strategy execution. 
        Refer to README for strategy breakdown.
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:

            # Run the 3 sub-tasks in parallel
            get_optimal_amount_ETH_task = executor.submit(Strategy.get_optimal_amount_ETH, pool_a, pool_b)
            get_fast_gas_price_task = executor.submit(Strategy.get_fast_gas_price)
            get_gas_used_task = executor.submit(Strategy.get_gas_used)

            # Get result once sub-tasks are done
            optimal_amount_ETH, amount_ETH_earned = get_optimal_amount_ETH_task.result()
            fast_gas_price = get_fast_gas_price_task.result()
            gas_used = get_gas_used_task.result()
        
            # Strategy is profitable if total revenue > total cost (in ETH)
            total_revenue = amount_ETH_earned * pow(10,18)
            total_cost = fast_gas_price * gas_used * pow(10,9)

            # Return if the strategy is profitable, and the optimal ETH amount of True.
            is_profitable, optimal_amount_ETH = (True, optimal_amount_ETH) if total_revenue > total_cost else (False, 0)
            profit_margin_pct = round((total_revenue-total_cost)/total_revenue*100, 2) if total_revenue > 0 else 0
            print(f"Strategy Outcome: Profitable - {is_profitable}, Optimal Amount - {optimal_amount_ETH} ETH, Profit Margin - {profit_margin_pct}%")
            return (is_profitable, optimal_amount_ETH)
        




        


