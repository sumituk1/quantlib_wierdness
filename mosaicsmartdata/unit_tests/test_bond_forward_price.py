import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '../..'))

import unittest
from risk.bond_mod_duration import *
from risk.bond_forward_price import *
import numpy as np
from risk.bond_ytm import bond_ytm
from risk.bond_price import bond_price
from common.constants import DayCountConv, CalendarFactory, Frequency
from datetime import datetime
from risk.schedule import CSchedule

class TestBondForwardPrice(unittest.TestCase):

    def test_forward_UST5y_without_coupon(self):
        TOLERANCE = 1e-2

        # ==== input =====
        price = 99.97656250  # spot settle clean price
        spot_settle_date = "2016-08-09"  # settle date
        coupon = 1.125  # bond coupon
        frequency = "S"  # coupon frequency
        next_coupon_date = "2017-01-31"  # next coupon date
        prev_coupon_date = "2016-07-31"  # previous coupon date
        forward_date = "2016-08-16"  # forward settle date
        daycount = "ACT/ACT"  # daycount convention
        repo = +0.49  # repo rate in %

        forward_price = govbondforwardprice(price, spot_settle_date, prev_coupon_date, next_coupon_date,
                                            forward_date, coupon, frequency, repo)

        self.assertLessEqual(np.abs(forward_price - 99.964691)/99.964691, TOLERANCE, msg=None)

    def test_forward_UST5y_with_coupon(self):
        TOLERANCE = 1e-2

        # ==== input ===== EMC 2.65 06/01/20 Corp
        price = 98.823000  # spot settle clean price
        spot_settle_date = "2015-11-25"  # settle date
        coupon = 2.65  # bond coupon
        frequency = "S"  # coupon frequency
        next_coupon_date = "2016-12-01"  # next coupon date
        prev_coupon_date = "2015-06-01"  # previous coupon date
        forward_date = "2015-12-04"  # forward settle date
        daycount = "ACT/ACT"  # daycount convention
        repo = +0.49  # repo rate in %

        forward_price = govbondforwardprice(price, spot_settle_date, prev_coupon_date, next_coupon_date,
                                            forward_date, coupon, frequency, repo)

        print("Forward price for US 5y with coupon =", forward_price)
        self.assertLessEqual(np.abs(forward_price - 98.768959) / 98.768959, TOLERANCE, msg=None)

    def test_duration_DE15y_without_coupon(self):
        TOLERANCE = 1e-2

        # ==== input =====
        price = 178.255000  # spot settle clean price
        spot_settle_date = "2016-08-10"  # settle date
        coupon = 5.5 # bond coupon
        frequency = "A"  # coupon frequency
        next_coupon_date = "2017-01-04"  # next coupon date
        prev_coupon_date = "2016-01-04"  # previous coupon date
        forward_date = "2016-08-17"  # forward settle date
        daycount = "ACT/ACT"  # daycount convention
        repo = -0.298  # repo rate in %

        forward_price = govbondforwardprice(price, spot_settle_date, prev_coupon_date, next_coupon_date,
                                            forward_date, coupon, frequency, repo)

        print("Forward price for DE 15y without coupon =", forward_price)
        self.assertLessEqual(np.abs(forward_price - 178.139289) / 178.139289, TOLERANCE, msg=None)

    def test_duration_DE15y_with_coupon(self):
        TOLERANCE = 1e-2
        # ==== input =====
        price = 114.745000  # spot settle clean price
        spot_settle_date = "2015-10-20"  # settle date
        coupon = 1.625  # bond coupon
        frequency = "A"  # coupon frequency
        next_coupon_date = "2015-10-24"  # next coupon date
        prev_coupon_date = "2014-10-24"  # previous coupon date
        forward_date = "2015-10-28"  # forward settle date
        daycount = "ACT/ACT"  # daycount convention
        repo = -0.298  # repo rate in %

        forward_price = govbondforwardprice(price, spot_settle_date, prev_coupon_date, next_coupon_date,
                                            forward_date, coupon, frequency, repo)
        print("Forward price for DE 15y with coupon =", forward_price)
        self.assertLessEqual(np.abs(forward_price - 114.701754) / 114.701754, TOLERANCE, msg=None)


if __name__ == '__main__':
    unittest.main()