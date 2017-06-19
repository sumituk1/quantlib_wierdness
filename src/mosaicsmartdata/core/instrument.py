from mosaicsmartdata.common.constants import Currency, Country
from mosaicsmartdata.core.generic_parent import GenericParent
from mosaicsmartdata.core.discounting_service import DiscountingService

class Instrument(GenericParent):
    def __init__(self, *args, **kwargs):
        self.sym = None
        self.ccy = None
        self.tenor = None
        self.venue = None
        self.holidayCities = None

class FXInstrument(Instrument):
    def __init__(self, *args, **kwargs):
        # ccy is base currency,
        self.ccy2 = None
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

class FXForward(FXInstrument):
    def __init__(self, *args, **kwargs):
        self.notional1 = None # includes sign, + means I'm getting that flow
        self.notional2 = None # includes sign, + means I'm getting that flow
        self.settle_date = None
        self.isSpot = True
        self.isDeliverable = True
        self.disc = DiscountingService()
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

    def spot(self):
        return abs(self.notional2/self.notional1)

    def pv(self):
        return self.notional1*self.disc(self.settle_date,self.ccy) - self.notional2*self.disc(self.settle_date,self.ccy2)

class FXSwap(FXInstrument):
    def __init__(self, leg1: FXForward, leg2: FXForward, **kwargs):
        self.leg1 = leg1
        self.leg2 = leg2
        if not (leg1.ccy == leg2.ccy and leg1.ccy2 == leg2.ccy2):
            raise ValueError('The two legs of an FX swap must have the same ccy pair')

        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        for key in self.__dict__.keys():
            if key in self.leg1.__dict__ and key in self.__dict__ \
                and self.__dict__[key] is None and key not in ['sym','tenor']:
                    self.__dict__[key] = self.leg1.__dict__[key]

    def forward_points(self):
            return self.leg2.spot() - self.leg1.spot()

    def pv(self):
        return self.leg1.pv() + self.leg2.pv()

    def __getattr__(self, item):
        if item in self.leg1.__dict__:
            return self.leg1.__dict__[item]
        else:
            return AttributeError('FXSwap doesn''t have attribute ', item)

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