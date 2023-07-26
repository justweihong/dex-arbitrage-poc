import sys
sys.path.append("../source")
from Pool import Pool

class PoolStub(Pool):
    def __init__(self, reserve_DAI: int, reserve_ETH: int):
        self.reserve_DAI = reserve_DAI
        self.reserve_ETH = reserve_ETH