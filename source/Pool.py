from web3 import Web3

class Pool:
    """
    Serve to interact with the DAI/ETH pair reserves and store data in memory.
    """
    def __init__(self, pool_name, rpc_ws_url: str, contract_addr: str, contract_abi: str):
        self.pool_name = pool_name
        w3 = Web3(Web3.WebsocketProvider(rpc_ws_url))
        self.pair_contract = w3.eth.contract(address=contract_addr, abi=contract_abi)
        self.reserve_DAI = None
        self.reserve_ETH = None  

    def get_reserves(self):
        """
        Get the pool reserves.
        """
        return (self.reserve_DAI, self.reserve_ETH)
    
    def update_reserves(self):
        """
        Calls pair contract to get latest reserve amount and update pool.
        """
        self.reserve_DAI, self.reserve_ETH, _ = self.pair_contract.functions.getReserves().call()
        # round(self.reserve_DAI/pow(10,18), 2):,
        print(f"INFO: {self.pool_name}'s reserve updated (DAI: {round(self.reserve_DAI/pow(10,18), 2):,}, ETH: {round(self.reserve_ETH/pow(10,18), 2):,}). Price: {round(self.reserve_DAI/self.reserve_ETH, 2)} DAI/ETH")