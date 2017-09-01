from unittest import TestCase
import pickle
import datetime
from mosaicsmartdata.core.curve_utils import construct_OIS_curve, get_rate, discounting_factor, curve_from_disc_factors


class TestCurves(TestCase):
    def test_disc_factor_curve(self):
        # convert a list of discounting factors into a curve and back
        spot_date = datetime.date(2017, 9, 4)
        maturity_dates = [ spot_date + datetime.timedelta(days=7*i) for i in range(1,4)]
        disc_factors = [ 1 + 0.01 * i for i in range(0.3)]
        inputs = [ (df, spot_date, end) for df, end in zip(maturity_dates,disc_factors)]
        curve = curve_from_disc_factors(inputs)
        for md, df in zip(maturity_dates, disc_factors):
            this_df = discounting_factor(curve,spot_date,md)
            self.assertEqual(this_df, df)

    def test_ois_curve(self):
        spot_date = datetime.date(2017, 9, 4)
        maturity_dates = [spot_date + datetime.timedelta(days=7 * i) for i in range(1, 4)]
        ois_rates = [1 + 0.01 * i for i in range(1,4)]
        rate_dict = {}
        for md, rate in zip(maturity_dates,ois_rates):
            rate_dict[(spot_date,md)] = rate

        curve = construct_OIS_curve(rate_dict)
        for md, rate in zip(maturity_dates,ois_rates):
            self.assertEqual(rate, get_rate(curve, spot_date, md))

if __name__ == '__main__':
    #    unittest.main()
    k= TestCurves()
    #k.setUp()
    k.detailed_test_pricing_context()