from collections import namedtuple
from copy import copy

from mosaicsmartdata.common.constants import Country
from mosaicsmartdata.core.date_calculator import DateCalculator
from mosaicsmartdata.core.generic_parent import GenericParent
from mosaicsmartdata.core.instrument_static_singleton import InstrumentStaticSingleton

TenorTuple = namedtuple('TenorTuple','tenor today instr')
SpotRate = namedtuple('SpotRate','ccy1  ccy2 today spot_date mid')

date_calc = DateCalculator()


class PricingContext:
    def __init__(self, curves, spots, timestamp):
        '''
        A bundle of spot rates and matching discounting curves, derived from the
        FX spot and swap markets
        :param curves: a dict of discounting curves by ccy, implied from the FX swap market
        :param spots: a dict of spot rates, with all currency pairs normalized to ccy1 = USD
        '''
        if 'USD' not in curves:
            raise ValueError('Need a USD discounting curve')

        self.curve = curves
        self.timestamp = timestamp
        self.today = timestamp.date()
        self.spot = spots
        self.spot['USD'] = 1

    def spot_rate(self, ccypair):
        if ccypair[0] in self.spot and ccypair[1] in self.spot:
            return self.spot[ccypair[1]]/self.spot[ccypair[0]]
        else:
            return float('NaN')

    def fwd_points(self, ccypair, start_date, end_date):
        # TODO: use discounting curves to derive correct forward points
        return float('NaN')


class Instrument(GenericParent):
    def __init__(self, *args, **kwargs):
        self.sym = None
        self.ccy = None
        self.tenor = None
        self.venue = None
        self.holidayCities = None
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

class FXInstrument(Instrument):
    pass

class FXForward(FXInstrument):
    def __init__(self, **kwargs):
        self.notionals = None # a pair of notionals includes sign, + means I'm getting that flow
        self.settle_date = None
        self.isDeliverable = True # only do cash FX for now
        self.date_calc = DateCalculator()
        self.static = InstrumentStaticSingleton()
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        self.pip_size = self.static.pip_size(self.ccy)
        self.maturity_date = self.settle_date

    def rate(self):
        return abs(self.notionals[1]/self.notionals[0])

    def price(self, pricing_context: PricingContext):
        # TODO: augment for forwards
        return pricing_context.spot_rate(self.ccy)

    def pv(self, pricingContext, today, accounting_ccy = 'USD', ignoreDiscountFromSpotToToday = True):
        if not self.is_spot(today):
            pass
            # if settle_date is not spot, discount notionals to spot
        # use pricingContext to convert both notionals to accounting_ccy
        # sum these up
        if not ignoreDiscountFromSpotToToday:
            pass
            # further discount the net value to today
        return None

    def spot_date(self, today):
        return date_calc.spot_date('fx',self.ccy,today)

    def is_spot(self, today):
        return self.settle_date == self.spot_date(today)

    def equivalent_spot_instrument(self):
        # returns a spot-settled forward with the same exposure to spot rates
        pass

class FXMultiForward(FXInstrument):
    def __init__(self, legs, **kwargs):
        self.legs = legs
        for leg in legs[1:]:
            if not leg.ccy == self.legs[0].ccy:
                raise ValueError('All the legs must have the same currency pair!')
        # TODO: get parent properties from first leg properties?
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        self.ccy = self.legs[0].ccy # need to do this as else will inherit default=None from Instrument
        #self.ccy = self.first_leg.ccy

    def pv(self,  pc: PricingContext):
        return sum([self.leg.pv(pc) for leg in self.legs])

    def __getattr__(self, item):
        if item in self.legs[0].__dict__:
            return self.legs[0].__dict__[item]
        else:
            return AttributeError('FXMultiForward doesn''t have attribute ', item)

# an FX Swap is just a multi-forward with just 2 legs
class FXSwap(FXInstrument):
    def __init__(self, legs, **kwargs):
        self.legs = legs
        if len(legs) >2:
            raise ValueError("An FXSwap only has 2 legs")
        for leg in legs[1:]:
            if not leg.ccy == self.legs[0].ccy:
                raise ValueError('All the legs must have the same currency pair!')
        # TODO: get parent properties from first leg properties?
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        self.ccy = self.legs[0].ccy # need to do this as else will inherit default=None from Instrument
        self.maturity_date = self.legs[1].settle_date
        self.settle_date = self.legs[0].settle_date

    def pv(self,  pc: PricingContext):
        return sum([self.leg.pv(pc) for leg in self.legs])

    def __getattr__(self, item):
        if item in self.legs[0].__dict__:
            return self.legs[0].__dict__[item]
        else:
            return AttributeError('FXMultiForward doesn''t have attribute ', item)

    def forward_points(self):
        return (self.legs[1].rate() - self.legs[0].rate())/self.pip_size()



class FixedIncomeInstrument(Instrument):
    def __init__(self, *args, **kwargs):
        self.par_value = 100
        self.spot_settle_date = None
        self.issue_date = None
        self.maturity_date = None
        self.duration = None# unit duration, per contract or $ notional
        self.coupon = None
        self.coupon_frequency = None
        self.day_count = None
        self.price_type = None
        self.country_of_risk = Country.US  # default to US
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))



class FixedIncomeIRSwap(FixedIncomeInstrument):
    def __init__(self, *args, **kwargs):
        self.float_coupon_frequency = None
        self.tenor = None
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

class OIS(FixedIncomeIRSwap):
    pass

class FixedIncomeBondFuture(FixedIncomeInstrument):
    def __init__(self, *args, **kwargs):
        self.contract_notional = None
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))


class FixedIncomeIRFuture(FixedIncomeInstrument):
    def __init__(self, *args, **kwargs):
        self.contract_notional = None
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

class FixedIncomeBond(FixedIncomeInstrument):
    def __init__(self, *args, **kwargs):
        self.is_benchmark = False
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

