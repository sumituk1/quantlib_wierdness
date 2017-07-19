from collections import namedtuple
from copy import copy

from mosaicsmartdata.common.constants import Country
from mosaicsmartdata.core.date_calculator import DateCalculator
from mosaicsmartdata.core.generic_parent import GenericParent
from mosaicsmartdata.core.instrument_singleton import InstrumentStaticSingleton

TenorTuple = namedtuple('TenorTuple','tenor today instr')
SpotRate = namedtuple('SpotRate','ccy1  ccy2 today spot_date mid')

class PricingContext:
    def __init__(self, curves, spots, today):
        '''
        A bundle of spot rates and matching discounting curves, derived from the
        FX spot and swap markets
        :param curves: a dict of discounting curves by ccy, implied from the FX swap market
        :param spots: a dict of spot rates, with all currency pairs normalized to ccy1 = USD
        '''
        if 'USD' not in curves:
            raise ValueError('Need a USD discounting curve')

        self.curve = copy.copy(curves)
        self.today = today
        self.spot = {}
        for s in spots:
            if s.ccy1 == 'USD':
                self.spot[s.ccy2] =s
            else:
                raise ValueError('Ccy1 must always be USD here, not ', s)

    def spot_rate(self, ccypair):
        # calculate the rate for that ccypair and return
        pass

    def fwd_points(self, ccypair, start_date, end_date):
        pass


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
        return self.date_calc.spot_date(self.ccy,today)

    def is_spot(self, today):
        return self.settle_date == self.spot_date(today)

    def equivalent_spot_instrument(self):
        # returns a spot-settled forward with the same exposure to spot rates
        pass

class FXMultiForward(FXInstrument):
    def __init__(self, legs, **kwargs):
        self.legs = legs
        self.first_leg = None
        for leg in legs:
            if not self.first_leg:
                self.first_leg = leg
            else:
                if not leg.ccy == self.first_leg.ccy:
                    raise ValueError('All the legs must have the same currency pair!')
        self.pip_size = InstrumentStaticSingleton().pip_size(self.first_leg)
        # TODO: get parent properties from first leg properties?
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))


    def pv(self,  pc: PricingContext):
        return sum([self.leg.pv(pc) for leg in self.legs])

    def __getattr__(self, item):
        if item in self.leg1.__dict__:
            return self.leg1.__dict__[item]
        else:
            return AttributeError('FXMultiForward doesn''t have attribute ', item)

# an FX Swap is just a multi-forward with just 2 legs
class FXSwap(FXMultiForward):
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

