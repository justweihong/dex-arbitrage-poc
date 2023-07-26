import os
import sys
import unittest
from dotenv import load_dotenv
from PoolStub import PoolStub
from parameterized import parameterized
sys.path.append("../source")
from Strategy import Strategy

class StrategyTest(unittest.TestCase):

    @parameterized.expand([
        (PoolStub(8500392609941613681523819, 4116472865721924711734) , PoolStub(7750392609941613681523819, 4126472865721924711734)), # 2,064.96 / 1,878.21
        (PoolStub(8120392609941613681523819, 4016472865721924711734) , PoolStub(7750392609941613681523819, 4126472865721924711734)), # 2,021.77 / 1,878.21
        (PoolStub(7820392609941613681523819, 4116472865721924711734) , PoolStub(7750392609941613681523819, 4126472865721924711734)), # 1,899.77 / 1,878.21
        ])
    def test_strategy_large_price_diff(self, pool_a, pool_b):
        """
        When pools have large price diff, the amount earned can exceed gas costs of executing function.
        Hence, strategy is profitable.
        """
        is_profitable, _ = Strategy.execute(pool_a, pool_b)
        self.assertTrue(is_profitable)

    @parameterized.expand([
        (PoolStub(7760392609941613681523819, 4116472865721924711734) , PoolStub(7750392609941613681523819, 4126472865721924711734)), # 1,885.20 / 1,878.21
        (PoolStub(7750392609941613681523819, 4116472865721924711734) , PoolStub(7750392609941613681523819, 4126472865721924711734)), # 1,882.77 / 1,878.21
        (PoolStub(7750392609941613681523819, 4125472865721924711734) , PoolStub(7750392609941613681523819, 4126472865721924711734)), # 1,878.66 / 1,878.21
        ])
    def test_strategy_small_price_diff(self, pool_a, pool_b):
        """
        When pools have small price diff, the amount earned is less than gas costs of executing function.
        Hence, strategy is not profitable.
        """
        is_profitable, _ = Strategy.execute(pool_a, pool_b)
        self.assertFalse(is_profitable)

    @parameterized.expand([
        (PoolStub(7743274327437243247324479, 4737346364263264362463) , PoolStub(7743274327437243247324479, 4737346364263264362463)), # 1,634.51/1,634.51
        (PoolStub(7820392609941613681523819, 4116472865721924711734) , PoolStub(7820392609941613681523819, 4116472865721924711734)), # 1,899.77/1,899.77
        (PoolStub(999999999999, 999999999999) , PoolStub(999999999999, 999999999999)) # 1/1
        ])
    def test_strategy_no_price_diff(self, pool_a, pool_b):
        """
        When pools have the same price, the amount earned = 0 and cannot cover the costs of executing function.
        Hence, strategy is not profitable.
        """
        is_profitable, _ = Strategy.execute(pool_a, pool_b)
        self.assertFalse(is_profitable)
        
        
if __name__ == '__main__':
    load_dotenv()
    unittest.main()