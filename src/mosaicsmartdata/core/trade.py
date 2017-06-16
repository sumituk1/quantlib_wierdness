import mosaicsmartdata.common.quantlib.bond.fixed_bond as bond
from mosaicsmartdata.common.quantlib.bond.bond_forward_price import govbond_cleanprice_from_forwardprice
from mosaicsmartdata.core.generic_parent import GenericParent
from mosaicsmartdata.core.instrument import FixedIncomeIRSwap, FixedIncomeBondFuture, FixedIncomeBond, FXForward, FXSwap
from mosaicsmartdata.core.repo_singleton import *


class Trade(GenericParent):
    def __init__(self, *args, **kwargs):
        self.trade_id = None
        self.package_id = None
        self.package = None # reference to the mother package
        self.paper_trade = False
        self.timestamp = None
        self.notional = None
        self.side = None
        self.traded_px = None
        self.adj_traded_px = None
        self.trade_date = None
        self.trade_settle_date = None
        self.client_sys_key = None
        self.trade_rc = None
        self.sales = None
        self.trader = None
        self.delta = None
        self.factor_risk = None
        self.leg_no = None
        self.package_size = None  # package_size of the trade executed

        # just paste this magic line in to assign the kwargs
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        if self.adj_traded_px  is None:
            self.adj_traded_px = self.traded_px
        # use this syntax to require non-None values for certain fields
        self.check_values(['trade_id'])

        if self.package_id is None:
            self.package_id = self.trade_id

    def markout_mults(self):
        return {'price': 1, 'PV': self.delta}

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        # calculate different markout types on the fly by applying the correct multiplier
        elif item in self.instrument.__dict__:
            return self.instrument.__dict__[item]
        else:
            raise AttributeError('This object doesn\'t have attribute' + item)

class FXForwardTrade(Trade):
    def __init__(self, *args, **kwargs):
        self.instrument = FXForward()
        kwargs = self.instrument.apply_kwargs(self.instrument.__dict__, kwargs)
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

class FXSwapTrade(Trade):
    def __init__(self, leg1, leg2, **kwargs):
        self.instrument = FXSwap(leg1, leg2)
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))


class FixedIncomeTrade(Trade):
    # Constructor
    def __init__(self, *args, **kwargs):
        self.bid_px = None
        self.ask_px = None
        self.mid_px = None
        #self.duration = None
        self.trade_added_to_rp = False
        self.is_d2d_force_close = False
        self.beta = dict()  # for hedging using multiple assets
        # the magic line to process the kwargs
        # other_args = self.apply_kwargs(self.__dict__,kwargs)
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))


    def calc_trade_delta(self):
        if self.delta is None:
            self.delta = self.duration * self.notional * 0.0001

    def markout_mults(self):
        return {'price': (1 / self.par_value) * self.notional,
                'PV': self.delta,
                'cents': 100.0,
                'bps': (1.0 / self.duration / self.par_value) * 10000}

class BondFuturesTrade(FixedIncomeTrade):
    def __init__(self, *args, **kwargs):
        self.instrument = FixedIncomeBondFuture()
        kwargs = self.instrument.apply_kwargs(self.instrument.__dict__, kwargs)

        self.maturity_date = None
        self.contracts = 0
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        self.notional *= self.contracts
        # First calculate the delta of a single Futures contract
        if self.delta is None:
            # futures delta per contract_size or notional
            self.delta = self.notional * self.duration * 0.0001

    def markout_mults(self):
        return {'price': (1 / self.par_value) * self.notional,
                'PV': self.delta,
                'cents': 100.0,
                'bps': (1.0 / self.duration / self.par_value) * 10000}


class InterestRateSwapTrade(FixedIncomeTrade):
    def __init__(self, *args, **kwargs):
        self.instrument = FixedIncomeIRSwap()
        kwargs = self.instrument.apply_kwargs(self.instrument.__dict__, kwargs)
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

    def markout_mults(self):
        if self.price_type == PriceType.Upfront:
            return {'price': (1 / self.par_value) * self.notional,
                    'PV': 1.0, # (1.0 / self.par_value) * 10000 * self.delta,
                    # 'cents': 100.0,
                    'bps': (1.0 / self.delta)}
        else:
            return {'price': (1 / self.par_value) * self.notional,
                    'PV': (1.0 / self.par_value) * 10000 * self.delta,
                    # 'cents': 100.0,
                    'bps': (1.0 / self.par_value) * 10000}


class FixedIncomeBondTrade(FixedIncomeTrade):
    def __init__(self, *args, **kwargs):
        self.repo_rate = RepoSingleton()
        self.instrument = FixedIncomeBond()
        kwargs = self.instrument.apply_kwargs(self.instrument.__dict__, kwargs)
        #self.par_value = 100
        #self.maturity_date = None
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        self.check_non_standard_trade()
        # set delta of hedge instrument
        if self.delta is None:
            # futures delta should always be passed in
            self.delta = self.duration * self.notional * 0.0001

    def markout_mults(self):
        return {'price': (1 / self.par_value) * self.notional,
                'PV': self.delta,
                'cents': 100.0,
                'bps': (1.0 / self.duration / self.par_value) * 10000}

    def check_non_standard_trade(self):
        self.adj_traded_px = self.traded_px
        # if isinstance(self.trade_settle_date, dt.datetime):
        #     self.trade_settle_date
        try:
            if self.trade_settle_date > self.spot_settle_date and not self.paper_trade:
                # trade_settle_date is a forward date. So calculate the price drop and adjust the traded_px
                # create a new attribute called adj_spot_px
                next_coupon_date = bond.getNextCouponDate(issue_date=self.issue_date,
                                                          maturity_date=self.maturity_date,
                                                          frequency=self.coupon_frequency,
                                                          holidayCities=self.holidayCities,
                                                          settle_date=self.trade_settle_date)

                prev_coupon_date = bond.getLastCouponDate(issue_date=self.issue_date,
                                                          maturity_date=self.maturity_date,
                                                          frequency=self.coupon_frequency,
                                                          holidayCities=self.holidayCities,
                                                          settle_date=self.trade_settle_date)

                self.adj_traded_px = govbond_cleanprice_from_forwardprice(forward_price=self.traded_px,
                                                                          spot_settle_date=self.spot_settle_date,
                                                                          prev_coupon_date=prev_coupon_date,
                                                                          next_coupon_date=next_coupon_date,
                                                                          forward_date=self.trade_settle_date,
                                                                          coupon=self.coupon,
                                                                          day_count=self.day_count,
                                                                          frequency=self.coupon_frequency,
                                                                          repo=self.repo_rate(ccy=self.ccy,
                                                                                              date=self.trade_date))
        except:
            pass
            # TODO add proper logging here
            # except:
            #     def check_non_standard_trade(self):
            #         self.adj_traded_px = self.traded_px




''' Interest Rate Swap product
Specific changes:
1. markout_mults - Since Swaps is yield based so no need to do price to yield conversion'''





if __name__ == '__main__':
    date_0 = dt.datetime(2017, 1, 2)
    time_0 = dt.time(10, 23)  # .strftime("%H:%M:%S")
    tr = Trade()
    tr.trade_id = '111'
    tr.sym = '9128235'
    tr.notional = 7000000
    tr.side = TradeSide.Bid
    tr.traded_px = 96.916
    tr.mid_px = 96.928
    tr.client_key = 111
    tr.duration = 8.92
    tr.on_repo = 0.02
    tr.trade_date = date_0
    tr.ccy = 'EUR'
    # tr.calculate_trade_dv01()
