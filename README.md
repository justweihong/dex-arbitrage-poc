# Table of Contents
- [Table of Contents](#table-of-contents)
- [1. Introduction](#1-introduction)
  - [1.1 Overview](#11-overview)
  - [1.2 Scope](#12-scope)
  - [1.4 Terminologies](#14-terminologies)
- [2. Technical Specifications](#2-technical-specifications)
- [3. Implementation Details](#3-implementation-details)
  - [3.1 Overview](#31-overview)
  - [3.2 Server](#32-server)
  - [3.3 Subscriber](#33-subscriber)
  - [3.4 Handler](#34-handler)
  - [3.5 Pool](#35-pool)
  - [3.6 Strategy](#36-strategy)
- [4. Arbitrage Strategy Approach](#4-arbitrage-strategy-approach)
  - [4.1. Overview](#41-overview)
  - [4.2 Determining the max amount of `ETH` that can be earned](#42-determining-the-max-amount-of-eth-that-can-be-earned)
  - [4.2.1 Determining Low and High Pools](#421-determining-low-and-high-pools)
  - [4.2.2 Determining The Output Amount of a Single Swap](#422-determining-the-output-amount-of-a-single-swap)
    - [4.2.3 Determine The Output Amount of Two Swaps](#423-determine-the-output-amount-of-two-swaps)
    - [4.2.4 Considering Price Impact From Input Amount of `ETH`](#424-considering-price-impact-from-input-amount-of-eth)
    - [4.2.5 Determining the Optimal Amount of `ETH` to input](#425-determining-the-optimal-amount-of-eth-to-input)
  - [4.3 Gas Price](#43-gas-price)
  - [4.4 Gas Used (Not Implemented Yet)](#44-gas-used-not-implemented-yet)
- [5. Results Discussion](#5-results-discussion)
  - [5.1 Arbitrage Strategy](#51-arbitrage-strategy)
  - [5.2 Arbitrage Strategy benchmark](#52-arbitrage-strategy-benchmark)
- [6. Optimization Strategies](#6-optimization-strategies)
  - [6.1 Overview](#61-overview)
  - [6.2 Reducing Network Calls](#62-reducing-network-calls)
  - [6.3 Running Sub Tasks in Parallel](#63-running-sub-tasks-in-parallel)
- [7. Limitations](#7-limitations)
  - [7.1 Front-runners in Mempool](#71-front-runners-in-mempool)
  - [7.2 Price Slippage Uncertainty](#72-price-slippage-uncertainty)
  - [7.3 No Duplicate Pools in Same Network](#73-no-duplicate-pools-in-same-network)
- [8. Running This Project](#8-running-this-project)
- [9. Conclusion](#9-conclusion)

# 1. Introduction

## 1.1 Overview
This project aims to develop a program to identify of the arbitrage opportunities between to UniSwapV2 Pools (Pool A and Pool B), and calculate the amount of profit that can be derived from the **price diffference**.

## 1.2 Scope 
The scope of this project are limited to the following:
| No. | Category   | Scope            | Remarks                |
| --- |------------|------------------|------------------------|
|1    |Exchanges   |UniSwap DEX only. |CEXs (i.e. Binance, Coinbase, Kraken, OKEx, etc) are other DEXs (i.e. SushiSwap, PancakeSwap, Curve, etc) are not included.|
|2    |Version|UniSwap V2 only|Price calculation will be based on the [constant product formula](https://docs.uniswap.org/contracts/v2/concepts/protocol-overview/glossary#constant-product-formula) `x * y = k`. As for UniSwapV3, liquidity is concentrated within price ranges with customizable price rances set by liquidity providers (LPs). This allows more target efficient liquidity provision. However, arbitrage calculations are more complicated, hence only V2 is considered in this time frame so that it can be covered with more depth.|
|3|Network| Pool A and Pool B are assumed to be within the same network.| Hence, the arbitrage swaps can be executed within a single contract method and remain **atomic**. Arbitrages across different networks is possible, but executing an "atomic transaction" across network requires more consideration and will excluded in the scope of this project.|
|4|Token Swaps|Directly between `ETH` and `DAI` only.|While there are other possible routes with different costs across multiple token pairs (i.e. **ETH** -> BTC -> CRO -> **DAI**), only **direct price difference** between these two tokens will be considered to limit the scope and cover more depth.

## 1.4 Terminologies
- ETH: When token `ETH` is mentioned, it refers to Wrapped ETH (WETH). Since Ether itself is not in ERC-20 format, it is wrapped into a ERC-20 token so that it can be traded in DEXs.

# 2. Technical Specifications
The technical specifications of the project are as such:
  1. <u>Programming Language</u>: `Python`. 
   As the job scope primarily requires `Python`, and some `C++`, using `Python` would be appropriate for this project. 
  2. <u>Paradigm</u>:  `OOP`
   An Object-oriented programming paradigm will be used.
  3. <u>Libraries</u>: 
     * `Web3.py` - An alternative to `Web3.js` in `Python` language to interact with Ethereum.
     * `os` and `dotenv` - Abstract `.env` variables away from codebase.
     * `websockets` - Preferred over `http` connection because it is persistent and can continuously subscribe to network for updates in pools
     * `asyncio` - For use of asynchronouse methods.
     * `scipy` - Determine turning points to optimize profits during mathematical calculations.
     * `requests` and `json` - Calling `HTTP` endpoints formatting of responses.

# 3. Implementation Details

## 3.1 Overview
The strategy approach is to first connect to the network and subscribe to new blocks. Once a new block is mined,the two pools will have their reserves updated. The arbitrage strategy then executes to get the optimal amount of ETH earned after accounting for swap fees, and factor in the gas costs to determine overall profits (see [4. Arbitrage Strategy Approach](#4-arbitrage-strategy-approach) for in-depth details). The main components involved are:
  1. [Server](./source/Server.py) - Main server to set up pools, connecting to the network and executing the strategy.
  2. [Subscriber](./source/Subscriber.py) - Serves to interact with the network which the Liquidity Pools (LP) are deployed in, such as subscribing with new blocks.
  3. [Handler](./source/Handler.py) - Serves to handle events that are being published, such as a new block event.
  4. [Pool](./source/Pool.py) - Serve to interact with the DAI/ETH pair reserves and store data in memory.
  5. [Strategy](./source/Strategy.py) - Serves to execute the DEX price arbitrage strategy.

## 3.2 Server
The main server to set up pools, connecting to the network and executing the strategy. When running the main server, it starts by loading the environment variables, set up `pool_a` and `pool_b` to update pool reserves and store in memory. It also defines the `strategy`, `subscriber` and `handler`, and then runs the `subscriber` to subscribe for updates in the network.

## 3.3 Subscriber
The `subscriber` serves to interact with the network which the Liquidity Pools (LP) are deployed in, such as subscribing with new blocks. It uses the `rpc_ws_url` endpoint to establish a persistent WebSocket connection with the network. It calls thhe `eth_subscribe` method to continuously subscribe to new blocks events from the network, and triggers the `callback()` for every new block event.

## 3.4 Handler
The `handler` serves to handle events that are being published, such as a new block event. When handling a new block event, it does the following:
   *  Update `pool_a` and `pool_b` reserves by calling the pools' `update_reserve()` method
   *  Execute the strategy by calling the `strategy`'s `execute()` method to determing if strategy is profitable and if yes, what is the optimal amount of ETH to perform the swap.

## 3.5 Pool
The `pool` serve to interact with the `DAI/ETH` pair reserves and store data in memory. The pool contains the following methods:
   * `get_reserves()`: Get the pool reserves.
   *  `update_reserves()`: Calls pair contract to get latest reserve amount and update pool.

## 3.6 Strategy
The `strategy` serves to execute the DEX price arbitrage strategy. The strategy includes execution includes the following parts:
   *  `get_optimal_amount_ETH()`: Get the max `ETH` to earn based on the price difference between pools
   *  `get_fast_gas_price()`: Get the fast gas price (in Gwei) estimate minimize time taken for the arbitrage txn to be mined.
   *  `get_gas_used()`: Calculate gas used for contract to execute the arbitrage execution in the network.

The strategy approach will be further elaborate in below section.

# 4. Arbitrage Strategy Approach

## 4.1. Overview
Given an amount of `ETH`, an arbitrager who wants to **exploit the price difference** in on two `DAI/ETH` pools will want to buy `ETH` in the cheaper pool and sell `ETH` in the more expensive pool so that some `ETH` can be earned from the two swaps. However, there is a need to determine the costs associated from executing these swaps, which includes the **gas price** and the **gas used** for the strategy execution contract method. Hence, the profit of the strategy can be calculated as such: `profit = amount_ETH_earned - gas_price * gas_used`. The following sub-sections will cover the following:
   * Determining the max amount of `ETH` that can be earned
   * Gas Price
   * Gas Used

## 4.2 Determining the max amount of `ETH` that can be earned

## 4.2.1 Determining Low and High Pools
The reserves on `DAI/ETH` pair in UniSwapV2 is maintained in [constant product formula](https://docs.uniswap.org/contracts/v2/concepts/protocol-overview/glossary#constant-product-formula) `reserve_DAI * reserve_ETH = k`. Since the reserve of `ETH` is inversely proportional of `DAI`, the price of `ETH` in `DAI` are also inverse proportional as such: `price_of_ETH_in_DAI = reserve_DAI/ reserve_ETH`. 

As such, in `pool_a` and `pool_b`, the price of `ETH` in `DAI` can be caculated for both pools as such:
```python
pool_a_token_ETH_price = pool_a_reserve_DAI/pool_a_reserve_ETH
pool_b_token_ETH_price = pool_b_reserve_DAI/pool_b_reserve_ETH
```
And this will determine which of `pool_a` and `pool_b` becomes the `low_pool` and `high_pool`.
```python
if pool_a_token_ETH_price > pool_b_token_ETH_price:
    low_pool_reserve_DAI, low_pool_reserve_ETH = pool_b_reserve_DAI, pool_b_reserve_ETH
    high_pool_reserve_DAI, high_pool_reserve_ETH = pool_a_reserve_DAI, pool_a_reserve_ETH
else:
    low_pool_reserve_DAI, low_pool_reserve_ETH = pool_a_reserve_DAI, pool_a_reserve_ETH
    high_pool_reserve_DAI, high_pool_reserve_ETH = pool_b_reserve_DAI, pool_b_reserve_ETH
```

## 4.2.2 Determining The Output Amount of a Single Swap
Before performing calculations of two swaps, there is a need to first derive the calculations of a single swap. When executing a swap, when arbitrager inputs an amount `amount_ETH` of ETH, it will pay for the [0.3% swap fees](https://docs.uniswap.org/contracts/v2/concepts/protocol-overview/how-uniswap-works), so the input amount after including fees is: `amount_ETH_with_fees = 0.997 * amount_ETH`.

After accounting for fees, arbitrager will input `amount_ETH_with_fees` of ETH, and will swap for an output `amount_DAI` of DAI. As the constant `k` has to be maintained in the constant product formula such that `final_reserve_DAI = k / final_reserve_ETH`. The equation can be expanded and simplified as such:
```
final_reserve_DAI = k / final_reserve_ETH
(initial_reserve_DAI - amount_DAI) = (initial_reserve_DAI * initial_reserve_ETH) / (initial_reserve_ETH + amount_ETH_with_fees) # Substitute final reserve with initial reserve
amount_DAI = initial_reserve_DAI - (initial_reserve_DAI * initial_reserve_ETH) / (initial_reserve_ETH + amount_ETH_with_fees) # Set amount_DAI as LHS
amount_DAI = (initial_reserve_DAI*inital_reserve_ETH + initial_reserve_DAI*amount_ETH_with_fees - initial_reserve_DAI * initial_reserve_ETH) / (initial_reserve_ETH + amount_ETH_with_fees) # Adding initial_reserve_DAI into fraction
amount_DAI = (amount_ETH_with_fees * initial_reserve_DAI)/(initial_reserve_ETH + amount_ETH_with_fees)
```

Hence, `amount_DAI` can be simplified as `amount_DAI = (amount_ETH_with_fees * initial_reserve_DAI)/(initial_reserve_ETH + amount_ETH_with_fees)`. This equation is equivalent with [UniSwapV2's Library contract `getAmountOut()` method](https://github.com/Uniswap/v2-periphery/blob/master/contracts/libraries/UniswapV2Library.sol#L43-L50). 

### 4.2.3 Determine The Output Amount of Two Swaps
After determining the equation to get an output amount from an input amount from a swap, the arbitrager can execute a first swap from `ETH` to `DAI` from the cheaper `ETH` pool. After that, the arbitrager can use the amount of `DAI` obtained from the first swap to swap `DAI` back to `ETH` at the more expensive `ETH` pool, hence earning some amount of `ETH`. This can be implemented with the following code snippet:
```python
# First Swap: Swap ETH for DAI from high pool (in: ETH, out: DAI)
amount_ETH_with_fee = 0.997*amount_ETH*pow(10,18)
amount_DAI_out = ((amount_ETH_with_fee*high_pool_reserve_DAI)/(high_pool_reserve_ETH + amount_ETH_with_fee))/pow(10,18)

# Second Swap: Swap DAI for ETH from the low pool (in: DAI, out: ETH)
amount_DAI_with_fee = 0.997*amount_DAI_out*pow(10,18)
amount_ETH_out = ((amount_DAI_with_fee*low_pool_reserve_ETH)/(low_pool_reserve_DAI + amount_DAI_with_fee))/pow(10,18)
```

### 4.2.4 Considering Price Impact From Input Amount of `ETH`
Because of the constant product formula, the bigger input amount of `ETH` that is used to conduct the swap, the more significant it is compared to the total liquidity of the pool, hence resulting in [higher price impact](https://support.uniswap.org/hc/en-us/articles/8671539602317-What-is-Price-Impact-). That means that when prices impact is big, the amount of output token will reduce significantly and result in a loss from swap. As such, **there is a need to find the optimal amount of input `ETH`** such that after accounting for the price impact of the two swaps, it will result in the **max amount of `ETH` gained**.

### 4.2.5 Determining the Optimal Amount of `ETH` to input
In order to determine this, there is a need to try different amount of input `ETH`. However, simply doing brute force `for` loop from 0 to max tokens in the LP to find the maximum output amount will be too slow. By defining the equation in [code snippet from 4.3.2](#423-determine-the-output-amount-of-two-swaps) into a function, we can calculate the **max turning point** using the `minimize_scalar()` method from the `scipy.optimize` library as such:

```python
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

optimize_result = minimize_scalar(get_negative_amount_ETH_earned)
optimal_amount_ETH, amount_ETH_earned = optimize_result.x, -optimize_result.fun
```
With this, we can finally determine `optimal_amount_ETH`, optimal amount of `ETH` to input, and `amount_ETH_earned`, the max amount of `ETH` earned from the two swaps.

## 4.3 Gas Price
The execution of the arbitrage strategy will be from a contract method, and the transaction will be submitted to the mempool to be mined. However, only after it is mined then the transaction will be completed. If transaction are completed slowly, there is a risk that there are many other swaps already taken place in `pool_a` and `pool_b` beforehand and cause a change in reserves amount and hence price, resulting in the aribitrage calculation to be obselete and resulting in the arbitrager to lose money instead. Hence, there is a **need for arbitrage to complete the transaction as soon as possible**.

Miners are incentivised by the amount they earn from the gas costs paid by the arbitrager. This means that with **a higher gas prices** paid by the arbitrager, the faster the transaction will be completed. A high gas price that can be paid by the arbitrager can be estimated using [Etherscan's Gas Tracker API](https://docs.etherscan.io/api-endpoints/gas-tracker#get-gas-oracle) as such:
```python
api_key = os.getenv("ETHERSCAN_API_KEY")
endpoint = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={api_key}"
response = requests.get(endpoint)
fasGasPrice = json.loads(response.content)['result']['FastGasPrice']
```

## 4.4 Gas Used (Not Implemented Yet)
The execution of the arbitrage strategy will be from a contract method, and the total amount of gas used will depend on amount of computation required and the memory usage by the EVM. In order to get an estimate of the gas used, the contract containing the function has to be first deployed on the network, the [Web3.py's `estimate_gas()` method](https://web3py.readthedocs.io/en/v5/contracts.html#web3.contract.ContractFunction.estimate_gas) can be used.

# 5. Results Discussion
## 5.1 Arbitrage Strategy
When running this project, the environment variables set up for Pool A and Pool B are ETH/DAI pools for UniSwapV2 and SushiSwap on Ethereum mainnet respectively. As the price difference between the pools are too small, the revenue of the swap is not profitable after accounting for swap fees and gas costs. Here is a sample run:
```bash
INFO: New block mined -  17177475
INFO: Pool B's reserve updated (DAI: 3,957,504.44, ETH: 2,125.46). Price: 1861.95 DAI/ETH
INFO: Pool A's reserve updated (DAI: 7,741,999.43, ETH: 4,158.77). Price: 1861.61 DAI/ETH
Strategy Outcome: Profitable - False, Optimal Amount - 0 ETH, Profit Margin - 0%
INFO: New block mined -  17177476
INFO: Pool A's reserve updated (DAI: 7,741,999.43, ETH: 4,158.77). Price: 1861.61 DAI/ETH
INFO: Pool B's reserve updated (DAI: 3,957,504.44, ETH: 2,125.46). Price: 1861.95 DAI/ETH
Strategy Outcome: Profitable - False, Optimal Amount - 0 ETH, Profit Margin - 0%
```
Hence, a larger price difference is required for the strategy to be profitable. This can tested by benchmarking arbitrage strategy in the below section.

## 5.2 Arbitrage Strategy benchmark
The arbitrage strategy can be run across various price differences. The benchmark tests includes:
    1. Reserves with large ETH/DAI price difference (`2,064.96 / 1,878.21`, `2,021.77 / 1,878.21`, ` 1,899.77 / 1,878.21`)
    2. Reserves with small ETH/DAI price difference (`1,885.20 / 1,878.21`, `1,882.77 / 1,878.21`, ` 1,878.66 / 1,878.21`)
    3. Reserves with no ETH/DAI price difference (`1,634.51/1,634.51`, `1,899.77/1,899.77`,`1/1` )

Here is a sample run:
```bash
Strategy Outcome: Profitable - True, Optimal Amount - 89.52663232202653 ETH, Profit Margin - 99.89% # large diff
Strategy Outcome: Profitable - True, Optimal Amount - 67.78165385293339 ETH, Profit Margin - 99.8% # large diff
Strategy Outcome: Profitable - True, Optimal Amount - 5.573615653100916 ETH, Profit Margin - 69.85% # large diff
Strategy Outcome: Profitable - False, Optimal Amount - 0 ETH, Profit Margin - 0% # small diff
Strategy Outcome: Profitable - False, Optimal Amount - 0 ETH, Profit Margin - 0% # small diff
INFO: No turning points found, no profitable amount - Too many iterations..
Strategy Outcome: Profitable - False, Optimal Amount - 0 ETH, Profit Margin - 0% # small diff
Strategy Outcome: Profitable - False, Optimal Amount - 0 ETH, Profit Margin - 0% # no diff
Strategy Outcome: Profitable - False, Optimal Amount - 0 ETH, Profit Margin - 0% # no diff
Strategy Outcome: Profitable - False, Optimal Amount - 0 ETH, Profit Margin - 0% # no diff
----------------------------------------------------------------------
Ran 9 tests in 12.049s
```

# 6. Optimization Strategies

## 6.1 Overview
As many variables can change from the time the pool reserves is updated till the strategy has completed, there is a risk that there are many other swaps already taken place in `pool_a` and `pool_b` beforehand and cause a change in reserves amount and hence price, resulting in the aribitrage calculation to be obselete and resulting in the arbitrager to lose money instead. Hence, **the strategy calculation should be done as fast as possible**.

## 6.2 Reducing Network Calls
Network calls requires a conection and usually cause additional network overhead. For example, when determining the output amount of a single swap, although the [UniSwapV2's Library contract `getAmountOut()` method](https://github.com/Uniswap/v2-periphery/blob/master/contracts/libraries/UniswapV2Library.sol#L43-L50) can be used, it incurs the overhead to send the query to the node provider and waiting for the result of the Library contract query. The method is **`pure`**, which means it is **does not require any state** from the contract, and **the mathematical calculations can be calculated locally** as seen in [code snippet 4.2.2](#422-determining-the-output-amount-of-a-single-swap).

## 6.3 Running Sub Tasks in Parallel
Tasks that do not depend on each other can be executed in parallel. When the `handler` handles a new block event, pools update will require a network call which incurs over head as mentioned earlier. Since the `pool_a` and `pool_b` update do not depend on each other, they can be **executed in parallel** using `concurrent.futures`:
```python
# Update both pools in parallel
update_pool_a_task = executor.submit(self.pool_a.update_reserves)
update_pool_b_task = executor.submit(self.pool_b.update_reserves)
concurrent.futures.wait([update_pool_a_task, update_pool_b_task])
```

Also, the strategy execution consist of 3 sub tasks (getting max ETH, getting gas price and getting gas used) which do not depend on each other. Hence, they can also **executed in parallel** as such:

```python
 # Run the 3 sub-tasks in parallel
get_optimal_amount_ETH_task = executor.submit(Strategy.get_optimal_amount_ETH, pool_a, pool_b)
get_fast_gas_price_task = executor.submit(Strategy.get_fast_gas_price)
get_gas_used_task = executor.submit(Strategy.get_gas_used)
```

# 7. Limitations

## 7.1 Front-runners in Mempool
Mempool transactions are **public** and can be queries by [subscribing to pending transactions](https://web3js.readthedocs.io/en/v1.2.7/web3-eth-subscribe.html#subscribe-pendingtransactions). In the case of this project where DEX price arbitrages are conduct between pools of the same network. Any rational front-runners can detect these arbitrage transactions that are still in the mempool and **replicate the swap and offer a higher gas price** as long as the gas costs are still lower from the profit from tokens gained. Miners will then prioritise their transactions which will lead to the reserves prices to be outdated and might cause the original arbitrage swap to lose transactions instead.

## 7.2 Price Slippage Uncertainty
In contrast to **price impact**  discussed earlier in [section 4.2.4](#424-considering-price-impact-from-input-amount-of-eth), **price slippage** is not directly caused by the arbitrage transactions. Instead, it is caused by the [broad movement of the market](https://support.uniswap.org/hc/en-us/articles/8643879653261-What-is-Price-Slippage-). The collective movement on the liquidity can affect the profitability of the trade as well. Although this can be reduced by **lowering the price slippage tolerance** when execuring the arbitrage, it also **inrease the risk of transactions reverting**. Hence, the uncertainty of price slippage needs to be considered when executing the arbitrage as well.

## 7.3 No Duplicate Pools in Same Network
For UniswapV2, the deployed factory contract in each network will keep track of pairs and [only one unique pair exists](https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Factory.sol#L27) that is actively trading. A more realistic **DEX arbitrage strategy** of the **same direct pool** would be **between DEXs** and not same DEX, such as between UniSwap and SushiSwap. The environment variables provided for the project have Pool A as UniSwap's DAI/ETH pair and Pool B as SushiSwap's DAI/ETH pair


# 8. Running This Project
The strategy can be runned at the `'/source'` directory with the following CLI command:
```bash
python Server.py
```

The arbitrage strategy benchmark can be runned at the `'/test'` directory with the following CLI command:
```bash
python StrategyTest.py
```

# 9. Conclusion
This has been a rather interesting project. Please let me know if you have any feedback for me.
