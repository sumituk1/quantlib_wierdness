from unittest import TestCase
import pickle
import datetime
from mosaicsmartdata.core.curve_utils import construct_OIS_curve, get_rate, discounting_factor, curve_from_disc_factors


class TestCurves(TestCase):
    def test_disc_factor_curve(self):
        # convert a list of discounting factors into a curve and back
        # spot_date = datetime.date(2017, 9, 4)
        # maturity_dates = [ spot_date + datetime.timedelta(days=7*i) for i in range(1,4)]
        # disc_factors = [ 1 + 0.01 * i for i in range(0.3)]
        # inputs = [ (df, spot_date, end) for df, end in zip(maturity_dates,disc_factors)]

        spot_date = datetime.date(2017, 9, 21)
        maturity_dates = [datetime.date(2017, 10, 23), datetime.date(2017, 11, 21), datetime.date(2017, 12, 21)]
        ois_rates = [1.1440, 1.1490, 1.162]
        rate_dict = {}
        for md, rate in zip(maturity_dates, ois_rates):
            rate_dict[(spot_date, md)] = rate

        # 1. Bootstrap the OIS curve from the rates
        ois_curve = construct_OIS_curve(rate_dict)

        # 2. Get the disc factors
        discount_factors = dict() # store the discount factors by end_date
        for t in maturity_dates:
            discount_factors[t] = discounting_factor(ois_curve, t)

        # 3. Create a curve from discount factors
        maturity_dates =list( sorted(discount_factors.keys()))
        disc_factors = [discount_factors[key] for key in sorted(discount_factors.keys())]
        inputs = [(df, spot_date, end) for df, end in zip(disc_factors, maturity_dates)]
        ois_curve = curve_from_disc_factors(inputs)

        for md, rate in zip(maturity_dates, ois_rates):
            self.assertAlmostEqual(rate, get_rate(ois_curve, spot_date, md), places=4)
        # curve = curve_from_disc_factors(inputs)
        # for md, df in zip(maturity_dates, disc_factors):
        #     this_df = discounting_factor(curve,spot_date,md)
        #     self.assertEqual(this_df, df)

    def test_ois_curve(self):
        # spot_date = datetime.date(2017, 9, 4)
        # maturity_dates = [spot_date + datetime.timedelta(days=7 * i) for i in range(1, 4)]
        # ois_rates = [1 + 0.01 * i for i in range(1,4)]
        # rate_dict = {}
        # for md, rate in zip(maturity_dates,ois_rates):
        #     rate_dict[(spot_date,md)] = rate
        #
        # curve = construct_OIS_curve(rate_dict)
        spot_date = datetime.date(2017, 9, 21)
        maturity_dates = [datetime.date(2017,10,23), datetime.date(2017,11,21), datetime.date(2017,12,21)]
        ois_rates = [1.1440, 1.1490, 1.162]
        rate_dict = {}
        for md, rate in zip(maturity_dates, ois_rates):
            rate_dict[(spot_date, md)] = rate

        # 1. Bootstrap the OIS curve from the rates
        ois_curve = construct_OIS_curve(rate_dict)

        # 2. get the OIS rates from the bootstrapped curve
        #    This will be close but not exact to the input rates used for calibration
        for md, rate in zip(maturity_dates,ois_rates):
            self.assertAlmostEqual(rate, get_rate(ois_curve, spot_date, md), places=4)

if __name__ == '__main__':
    #    unittest.main()
    k= TestCurves()
    #k.setUp()
    k.detailed_test_pricing_context()