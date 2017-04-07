import unittest
import numpy as np
import mosaicsmartdata.common.quantlib.bond.fixed_bond as bond
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.quantlib.bond.bond_mod_duration import *


class TestBondDurationZSpread(unittest.TestCase):
    # test UST5y with no next_coupon_date
    def test_duration_UST5y(self):
        TOLERANCE = 15e-3
        # ==== input =====
        price = 100.203125
        settle_date = dt.datetime(2016, 8, 3)
        issueDate = dt.datetime(2014, 7, 25)  # -> python datetime
        maturity_date = dt.datetime(2021, 7, 31)
        holidayCities = HolidayCities.USA
        coupon = 1.125
        frequency = Frequency.SEMI
        daycount = DayCountConv.ACT_ACT
        # next coupon date (This is needed especially when there is a big short stub

        # next coupon date (This is needed especially when there is a big short stub)
        nextCouponDate = bond.getNextCouponDate(issue_date=issueDate,
                                                maturity_date=maturity_date,
                                                frequency=frequency,
                                                holidayCities=holidayCities,
                                                settle_date=settle_date)

        # nextCouponDate = dt.datetime(2017,1,31)
        duration = govbond_pvbp(price=price,
                                settle_date=settle_date,
                                next_coupon_date=nextCouponDate,
                                maturity_date=maturity_date,
                                coupon=coupon,
                                frequency=frequency,
                                day_count=daycount)

        self.assertLessEqual(np.abs(duration - 4.839) / 4.839, TOLERANCE, msg=None)

    def test_duration_UST10y(self):
        TOLERANCE = 1e-2
        # ==== input =====
        price = 100.75
        issue_date = dt.datetime(2014, 5, 15)
        settle_date = dt.datetime(2016, 8, 2)
        maturity_date = dt.datetime(2026, 5, 15)
        coupon = 1.625
        frequency = Frequency.SEMI
        holidayCities = HolidayCities.USA
        day_count = DayCountConv.ACT_ACT
        # nextCouponDate = dt.datetime(2017,11,15)
        nextCouponDate = bond.getNextCouponDate(issue_date=issue_date,
                                                maturity_date=maturity_date,
                                                frequency=frequency,
                                                holidayCities=holidayCities,
                                                settle_date=settle_date)

        duration = govbond_pvbp(price=price, settle_date=settle_date,
                                next_coupon_date=nextCouponDate, maturity_date=maturity_date,
                                coupon=coupon, frequency=frequency, day_count=day_count)

        self.assertLessEqual(np.abs(duration - 8.984) / 8.984, TOLERANCE, msg=None)

    def test_duration_UST30y(self):
        TOLERANCE = 1e-2
        # ==== input =====
        price = 104.78125
        settle_date = dt.datetime(2016, 8, 2)
        maturity_date = dt.datetime(2046, 5, 15)
        issue_date = dt.datetime(2014, 5, 15)
        coupon = 2.5
        frequency = Frequency.SEMI
        holidayCities = HolidayCities.USA
        day_count = DayCountConv.ACT_ACT

        # next coupon date (This is needed especially when there is a big short stub
        # nextCouponDate = dt.datetime(2017,11,15)
        nextCouponDate = bond.getNextCouponDate(issue_date=issue_date,
                                                maturity_date=maturity_date,
                                                frequency=frequency,
                                                holidayCities=holidayCities,
                                                settle_date=settle_date)

        duration = govbond_pvbp(price=price,
                                settle_date=settle_date,
                                next_coupon_date=nextCouponDate,
                                maturity_date=maturity_date,
                                coupon=coupon,
                                frequency=frequency,
                                day_count=day_count)

        self.assertLessEqual(np.abs((duration - 21.084) / 21.084), TOLERANCE, msg=None)

    def test_duration_DE10y(self):
        TOLERANCE = 15e-3
        # ==== input =====
        price = 100.1
        settle_date = dt.datetime(2017, 4, 9)
        maturity_date = dt.datetime(2027, 2, 15)
        issue_date = dt.datetime(2017, 1, 13)
        coupon = 0.25 # on a par value of 100
        frequency = Frequency.ANNUAL
        day_count = DayCountConv.ACT_ACT
        holidayCities = HolidayCities.EUR

        # nextCouponDate = dt.datetime(2017,8,15)
        next_coupon_date = bond.getNextCouponDate(issue_date=issue_date,
                                                  maturity_date=maturity_date,
                                                  frequency=frequency,
                                                  holidayCities=holidayCities,
                                                  settle_date=settle_date)

        duration = govbond_pvbp(price=price,
                                settle_date=settle_date,
                                next_coupon_date=next_coupon_date,
                                maturity_date=maturity_date,
                                coupon=coupon,
                                frequency=frequency,
                                day_count=day_count)

        self.assertLessEqual(np.abs(duration - 9.723) / 9.723, TOLERANCE, msg=None)

    def test_duration_IT30y(self):
        TOLERANCE = 3e-2
        # ==== input =====
        price = 101.187
        issue_date=dt.datetime(2015, 1, 22)
        settle_date = dt.datetime(2017, 4, 9)  # settle date
        maturity_date = dt.datetime(2046, 9, 1)
        coupon = 3.25
        frequency = Frequency.SEMI
        day_count = DayCountConv.ACT_ACT

        # nextCouponDate = dt.datetime(2017,8,15)
        next_coupon_date = bond.getNextCouponDate(issue_date=issue_date,
                                                  maturity_date=maturity_date,
                                                  frequency=frequency,
                                                  holidayCities=HolidayCities.EUR,
                                                  settle_date=settle_date)

        duration = govbond_pvbp(price=price,
                                settle_date=settle_date,
                                next_coupon_date=next_coupon_date,
                                maturity_date=maturity_date,
                                coupon=coupon,
                                frequency=frequency,
                                day_count=day_count)

        print("IT 30y benchmark duration = ", duration)
        self.assertLessEqual(np.abs(duration - 18.332) / 18.332, TOLERANCE, msg=None)

    # # Test case for a Annual Fixed Coupon Bond
    # def test_duration_Corp_DEDZ1J6X(self):
    #     TOLERANCE = 1e-2
    #     # =============================== input ===================================================================
    #     # 1. Creating a Fixed Coupon Bond Corp.....
    #     cusip = "DEDZ1J6X="
    #     issueDate = dt.datetime(2014, 7, 25)  # -> python datetime
    #     maturityDate = dt.datetime(2020, 7, 27)  # -> python datetime
    #     frequency = Frequency.ANNUAL  # -> Coupon Frequency
    #     holidayCities = HolidayCities.EUR  # -> Set the calendar
    #     daycount = DayCountConv.ACT_ACT  # -> Set the dayCount
    #     # businessConvention = ql.Unadjusted
    #     dateGeneration = ql.DateGeneration.Backward
    #     # monthEnd = False
    #     coupon = 0.7
    #     price = 101.988
    #     settleDate = dt.datetime(2017, 2, 10)
    #     nextCouponDate = bond.getNextCouponDate(issueDate, maturityDate, frequency,
    #                                             holidayCities, settleDate)
    #     print("next coupon date =%s" % nextCouponDate)
    #
    #     # 1. solve for the ytm of the bond
    #     ytm_corp = ytm.govbondytm(price, settleDate, nextCouponDate, maturityDate, coupon, frequency, daycount)
    #     print("YTM of corp:%s with price = %s is %s" % (cusip, price, ytm_corp))
    #     duration = mod_dur.govbondpvbp(price, settleDate, nextCouponDate, maturityDate,
    #                                    coupon, frequency, daycount, dy=0.0001)
    #     # 2. Calculate PVBP for the Bond
    #     print("duration of corp:%s is %s" % (cusip, duration))
    #     self.assertLessEqual(np.abs(duration - 3.414) / 3.414, TOLERANCE,
    #                          msg="Calculated duration=%s vs expected =%s" % (duration, 3.414))
    #     self.assertLessEqual(np.abs(ytm_corp * 100 - 0.123), TOLERANCE, msg=None)
    #
    # # Test ZSpread for a Annual Fixed Coupon Bond
    # def test_ZSpread_Corp_DEDZ1J6X(self):
    #     TOLERANCE = 5e-2
    #     # =============================== input ===================================================================
    #     # 1. Creating a Fixed Coupon Bond Corp.....
    #     cusip = "DEDZ1J6X="
    #     issueDate = dt.datetime(2014, 7, 25)  # -> python datetime
    #     maturityDate = dt.datetime(2020, 7, 27)  # -> python datetime
    #     frequency = Frequency.ANNUAL  # -> Coupon Frequency
    #     holidayCities = HolidayCities.EUR  # -> Set the calendar
    #     daycount = DayCountConv.ACT_ACT  # -> Set the dayCount
    #     # businessConvention = ql.Unadjusted
    #     dateGeneration = ql.DateGeneration.Backward
    #     # monthEnd = False
    #     coupon = 0.7
    #     price = 101.988
    #     settleDate = dt.datetime(2017, 2, 10)
    #     nextCouponDate = bond.getNextCouponDate(issueDate, maturityDate, frequency,
    #                                             holidayCities, settleDate)
    #     print("next coupon date =%s" % nextCouponDate)
    #
    #     # 1. solve for the ytm of the bond
    #     ytm_corp = bond_ytm.govbondytm(price, settleDate, nextCouponDate, maturityDate, coupon, frequency, daycount)
    #     print("YTM of corp:%s with price = %s is %s" % (cusip, price, ytm_corp))
    #     duration = mod_dur.govbondpvbp(price, settleDate, nextCouponDate, maturityDate,
    #                                    coupon, frequency, daycount, dy=0.0001)
    #     # 2. Get the benchmark Bond
    #     # ==========================
    #     cusip = "DE113541="
    #     issueDate = dt.datetime(2010, 8, 20)  # -> python datetime
    #     maturityDate = dt.datetime(2020, 9, 4)  # -> python datetime
    #     frequency = Frequency.ANNUAL  # -> Coupon Frequency
    #     holidayCities = HolidayCities.EUR  # -> Set the calendar
    #     daycount = DayCountConv.ACT_ACT  # -> Set the dayCount
    #     # businessConvention = ql.Unadjusted
    #     dateGeneration = ql.DateGeneration.Backward
    #     # monthEnd = False
    #     coupon = 2.25
    #     price = 110.678
    #     settleDate = dt.datetime(2017, 2, 10)
    #
    #     nextCouponDate = bond.getNextCouponDate(issueDate, maturityDate, frequency, holidayCities, settleDate)
    #     ytm_benchmark = bond_ytm.govbondytm(price, settleDate, nextCouponDate, maturityDate, coupon, frequency,
    #                                         daycount)
    #
    #     zspread = (ytm_corp - ytm_benchmark) * 10000
    #
    #     self.assertLessEqual(np.abs(zspread - 86.5) / 100, TOLERANCE,
    #                          msg="Calculated zspread=%s vs expected =%s" % (zspread, 86.5))
    #
    # # Test case for a Annual Fixed Coupon Bond
    # def test_duration_Corp_LU045218791(self):
    #     TOLERANCE = 1e-2
    #     # =============================== input ===================================================================
    #     # 1. Creating a Fixed Coupon Bond Corp.....
    #     cusip = "LU045218791="
    #     issueDate = dt.datetime(2009, 9, 17)  # -> python datetime
    #     maturityDate = dt.datetime(2022, 9, 14)  # -> python datetime
    #     frequency = Frequency.ANNUAL  # -> Coupon Frequency
    #     holidayCities = HolidayCities.EUR  # -> Set the calendar
    #     daycount = DayCountConv.ACT_ACT  # -> Set the dayCount
    #     # businessConvention = ql.Unadjusted
    #     dateGeneration = ql.DateGeneration.Backward
    #     # monthEnd = False
    #     coupon = 5.0
    #     price = 124.072
    #     settleDate = dt.datetime(2017, 2, 10)
    #     nextCouponDate = bond.getNextCouponDate(issueDate, maturityDate, frequency,
    #                                             holidayCities, settleDate)
    #     print("next coupon date =%s" % nextCouponDate)
    #
    #     # 1. solve for the ytm of the bond
    #     ytm_corp = ytm.govbondytm(price, settleDate, nextCouponDate, maturityDate, coupon, frequency, daycount)
    #     print("YTM of corp:%s with price = %s is %s" % (cusip, price, ytm_corp))
    #     duration = mod_dur.govbondpvbp(price, settleDate, nextCouponDate, maturityDate,
    #                                    coupon, frequency, daycount, dy=0.0001)
    #     # 2. Calculate PVBP for the Bond
    #     print("duration of corp:%s is %s" % (cusip, duration))
    #     self.assertLessEqual(np.abs(duration - 4.977) / 4.977, TOLERANCE,
    #                          msg="Calculated duration=%s vs expected =%s" % (duration, 3.414))
    #     self.assertLessEqual(np.abs(ytm_corp * 100 - 0.608), TOLERANCE, msg=None)
    #
    # # Test ytm/ duration and ZSpread for a US 30yr Annual Fixed Coupon Bond
    # def test_ZSpread_Corp_460146CQ4(self):
    #     TOLERANCE = 8e-2
    #     # =============================== input ===================================================================
    #     # 1. Creating a Fixed Coupon Bond Corp.....
    #     cusip = "460146CQ4="
    #     issueDate = dt.datetime(2016, 8, 11)  # -> python datetime
    #     maturityDate = dt.datetime(2047, 8, 15)  # -> python datetime
    #     frequency = Frequency.SEMI  # -> Coupon Frequency
    #     holidayCities = HolidayCities.USA  # -> Set the calendar
    #     daycount = DayCountConv.Thirty360_US  # -> Set the dayCount
    #     # businessConvention = ql.Unadjusted
    #     dateGeneration = ql.DateGeneration.Backward
    #     # monthEnd = False
    #     coupon = 4.4
    #     price = 96.2481
    #     settleDate = dt.datetime(2017, 2, 10)
    #     nextCouponDate = bond.getNextCouponDate(issueDate, maturityDate, frequency,
    #                                             holidayCities, settleDate)
    #     print("next coupon date =%s" % nextCouponDate)
    #
    #     # 1. solve for the ytm of the bond
    #     ytm_corp = bond_ytm.govbondytm(price, settleDate, nextCouponDate, maturityDate, coupon, frequency, daycount)
    #     print("YTM of corp:%s with price = %s is %s" % (cusip, price, ytm_corp))
    #     duration = mod_dur.govbondpvbp(price, settleDate, nextCouponDate, maturityDate,
    #                                    coupon, frequency, daycount, dy=0.0001)
    #     # print (duration)
    #     # 2. Get the latest 30yr OTR UST benchmark Bond
    #     # ==============================================
    #     cusip = "912810RU4="
    #     issueDate = dt.datetime(2016, 11, 15)  # -> python datetime
    #     maturityDate = dt.datetime(2046, 11, 15)  # -> python datetime
    #     frequency = Frequency.SEMI  # -> Coupon Frequency
    #     holidayCities = HolidayCities.USA  # -> Set the calendar
    #     daycount = DayCountConv.ACT_ACT  # -> Set the dayCount
    #     # businessConvention = ql.Unadjusted
    #     dateGeneration = ql.DateGeneration.Backward
    #     # monthEnd = False
    #     coupon = 2.875
    #     price = 98
    #     settleDate = dt.datetime(2017, 2, 10)
    #
    #     nextCouponDate = bond.getNextCouponDate(issueDate, maturityDate, frequency, holidayCities, settleDate)
    #     ytm_benchmark = bond_ytm.govbondytm(price, settleDate, nextCouponDate, maturityDate,
    #                                         coupon, frequency, daycount)
    #
    #     zspread = (ytm_corp - ytm_benchmark) * 10000
    #     self.assertLessEqual(np.abs(duration - 16.3) / 16.3, TOLERANCE,
    #                          msg="Calculated duration=%s vs expected =%s" % (duration, 16.3))
    #     self.assertLessEqual(np.abs(zspread - 172.5) / 100, TOLERANCE,
    #                          msg="Calculated zspread=%s vs expected =%s" % (zspread, 172.5))

if __name__ == '__main__':
    unittest.main()
