import unittest
from mosaicsmartdata.common.quantlib.bond.bond_mod_duration import *
from mosaicsmartdata.common.quantlib.bond.bond_forward_price import *
import numpy as np
from mosaicsmartdata.common.quantlib.bond.bond_ytm import *
from mosaicsmartdata.common.quantlib.bond.bond_price import *
from mosaicsmartdata.common.constants import DayCountConv, CalendarFactory, Frequency
from mosaicsmartdata.core.repo_singleton import *
from datetime import datetime
from mosaicsmartdata.common.schedule import CSchedule


class TestBondForwardPrice(unittest.TestCase):
    def test_forward_UST5y_without_coupon(self):
        TOLERANCE = 1e-2

        # ==== input =====
        repo_rate = RepoSingleton()
        price = 99.97656250  # spot settle clean price
        settle_date = dt.datetime(2016, 8, 9)  # settle date
        issue_date = dt.datetime(2014, 1, 31)  # -> python datetime
        maturity_date = dt.datetime(2021, 1, 31)
        coupon = 1.125  # bond coupon
        holidayCities = HolidayCities.USA
        frequency = Frequency.SEMI  # coupon frequency
        # next_coupon_date = dt.datetime(2017,1,31)
        # next coupon date (This is needed especially when there is a big short stub)
        next_coupon_date = bond.getNextCouponDate(issue_date=issue_date,
                                                  maturity_date=maturity_date,
                                                  frequency=frequency,
                                                  holidayCities=holidayCities,
                                                  settle_date=settle_date)

        prev_coupon_date = bond.getLastCouponDate(issue_date=issue_date,
                                                  maturity_date=maturity_date,
                                                  frequency=frequency,
                                                  holidayCities=holidayCities,
                                                  settle_date=settle_date)

        # prev_coupon_date = dt.datetime(2016, 7, 31)  # previous coupon date
        forward_date = dt.datetime(2016, 8, 16)  # forward settle date
        day_count = DayCountConv.ACT_ACT  # daycount convention
        repo = repo_rate(ccy=Currency.USD, date=settle_date)  # repo rate in %

        forward_price = govbond_forwardprice(price=price,
                                             spot_settle_date=settle_date,
                                             prev_coupon_date=prev_coupon_date,
                                             next_coupon_date=next_coupon_date,
                                             forward_date=forward_date,
                                             day_count=day_count,
                                             coupon=coupon,
                                             frequency=frequency,
                                             repo=repo)

        self.assertLessEqual(np.abs(forward_price - 99.964691) / 99.964691, TOLERANCE, msg=None)


    def test_duration_DE15y_without_coupon(self):
        TOLERANCE = 1e-2

        # ==== input =====
        repo_rate = RepoSingleton()
        price = 167.135  # spot settle clean price

        coupon = 5.5  # bond coupon
        frequency = Frequency.ANNUAL  # coupon frequency
        settle_date = dt.datetime(2017, 4, 11)  # settle date
        issue_date = dt.datetime(2000, 10, 27)  # -> python datetime
        maturity_date = dt.datetime(2031, 1, 4)
        forward_date = dt.datetime(2017,4,14)  # forward settle date
        day_count = DayCountConv.ACT_ACT  # daycount convention
        repo = repo_rate(ccy=Currency.EUR, date=settle_date)  # repo rate in %
        holidayCities=HolidayCities.EUR

        next_coupon_date = bond.getNextCouponDate(issue_date=issue_date,
                                                  maturity_date=maturity_date,
                                                  frequency=frequency,
                                                  holidayCities=holidayCities,
                                                  settle_date=settle_date)

        prev_coupon_date = bond.getLastCouponDate(issue_date=issue_date,
                                                  maturity_date=maturity_date,
                                                  frequency=frequency,
                                                  holidayCities=holidayCities,
                                                  settle_date=settle_date)

        forward_price = govbond_forwardprice(price=price,
                                             spot_settle_date=settle_date,
                                             prev_coupon_date=prev_coupon_date,
                                             next_coupon_date=next_coupon_date,
                                             forward_date=forward_date,
                                             day_count=day_count,
                                             coupon=coupon,
                                             frequency=frequency,
                                             repo=repo)

        print("Forward price for DE 15y without coupon =", forward_price)
        self.assertLessEqual(np.abs(forward_price - 167.0145) / 167.0145, TOLERANCE, msg=None)

    # def test_duration_DE15y_with_coupon(self):
    #     TOLERANCE = 1e-2
    #     # ==== input =====
    #     price = 114.745000  # spot settle clean price
    #     spot_settle_date = "2015-10-20"  # settle date
    #     coupon = 1.625  # bond coupon
    #     frequency = "A"  # coupon frequency
    #     next_coupon_date = "2015-10-24"  # next coupon date
    #     prev_coupon_date = "2014-10-24"  # previous coupon date
    #     forward_date = "2015-10-28"  # forward settle date
    #     daycount = "ACT/ACT"  # daycount convention
    #     repo = -0.298  # repo rate in %
    #
    #     forward_price = govbond_forwardprice(price, spot_settle_date, prev_coupon_date, next_coupon_date,
    #                                         forward_date, coupon, frequency, repo)
    #     print("Forward price for DE 15y with coupon =", forward_price)
    #     self.assertLessEqual(np.abs(forward_price - 114.701754) / 114.701754, TOLERANCE, msg=None)


if __name__ == '__main__':
    unittest.main()
