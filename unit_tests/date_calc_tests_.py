from unittest import TestCase
import pickle
import datetime
from mosaicsmartdata.core.date_calculator import DateCalculator

class TestDateCalc(TestCase):
    def setUp(self):
        self.date_calc = DateCalculator()
    def test_date_add(self):
        # TODO: I'm doing these tests in my head now, the 'correct' values may have to be corrected
        my_date = datetime.date(2017,9,3)# a Sunday
        self.assertEqual(self.date_calc.date_add(my_date, '0b'), datetime.date(2017, 9, 4))
        self.assertEqual(self.date_calc.date_add(my_date,'1b'), datetime.date(2017,9,5))
        self.assertEqual(self.date_calc.date_add(my_date,'2b'), datetime.date(2017,9,6))
        self.assertEqual(self.date_calc.date_add(my_date,'1w'), datetime.date(2017,9,11))
        self.assertEqual(self.date_calc.date_add(my_date, '1m'), datetime.date(2017, 10, 4))
        self.assertEqual(self.date_calc.date_add(my_date,'1y'), datetime.date(2018,10,4))


# if __name__ == '__main__':
#     #    unittest.main()
#     k= TestFX()
#     #k.setUp()
#     k.test_pricing_context_creation()