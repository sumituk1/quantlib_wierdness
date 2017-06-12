import numpy as np
from mosaicsmartdata.core.generic_parent import GenericParent
from mosaicsmartdata.core.repo_singleton import *
import mosaicsmartdata.common.quantlib.bond.fixed_bond as bond
from mosaicsmartdata.common.quantlib.bond.bond_forward_price import govbond_cleanprice_from_forwardprice


class Trade(GenericParent):
    def __init__(self, *args, **kwargs):
        self.repo_rate = RepoSingleton()
        self.trade_id = None
        self.package_id = None
        # self.package_size = None # todo: package_size is an attribute of FICC trade?
        self.paper_trade = False
        self.sym = None
        self.timestamp = None
        self.notional = None
        self.side = None
        self.traded_px = None
        self.trade_date = None
        self.trade_settle_date = None
        self.ccy = Currency.EUR
        self.client_sys_key = None
        self.trade_rc = None
        self.sales = None
        self.trader = None
        self.delta = None
        self.tenor = None
        self.venue = None
        self.holidayCities = None
        self.factor_risk = None
        self.country_of_risk = Country.US  # default to US

        # just paste this magic line in to assign the kwargs
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

        # use this syntax to require non-None values for certain fields
        self.check_values(['trade_id'])

        if self.package_id is None:
            self.package_id = self.trade_id

        def markout_mults(self):
            return {'price': 1, 'PV': self.delta}


class FixedIncomeTrade(Trade):
    # Attributes with default parameter.
    # # Instrument Static
    # coupon = 0.02
    # coupon_frequency = Frequency.SEMI
    # day_count = DayCountConv.ACT_365

    # Constructor
    def __init__(self, *args, **kwargs):
        self.is_benchmark = False
        self.bid_px = None
        self.ask_px = None
        self.mid_px = None
        self.duration = None
        self.trade_added_to_rp = False
        self.is_d2d_force_close = False
        self.beta = dict()  # for hedging using multiple assets
        self.par_value = 100
        self.spot_settle_date = None
        self.issue_date = None
        self.maturity_date = None
        self.coupon = None
        self.coupon_frequency = None
        self.float_coupon_frequency = None
        self.day_count = None
        self.leg_no = None
        self.price_type = None
        self.package_size = None  # package_size of the trade executed

        # the magic line to process the kwargs
        # other_args = self.apply_kwargs(self.__dict__,kwargs)
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

        self.calc_trade_delta()
        # if self.delta is None:
        #     self.delta = self.duration * self.notional * 0.0001

        # check if this is a non-standard trade
        self.check_non_standard_trade()

    def calc_trade_delta(self):
        if self.delta is None:
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


class FixedIncomeFuturesHedge(Trade):
    def __init__(self, *args, **kwargs):
        # self.package_id = None
        self.min_hedge_delta = 1000  # in relevant ccy
        # self.trade = None
        self.duration = None  # <- hedge trade attribute for the time being
        self.trade_delta = None  # <- hedge trade_delta attribute for the time being
        self.trade_beta = dict()
        self.package_size = None  # package_size of the trade executed
        self.leg_no = None  # -1 would be the package leg . 0/1/2/3 are the leg_Nos
        self.price_type = None

        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        # self.notional = 100000  # for futures
        self.paper_trade = True
        self.par_value = 100
        self.maturity_date = None
        self.hedge_contracts = 0
        self.adj_traded_px = self.traded_px
        # self.notional = 0.0

        # First calculate the delta of a single Futures contract
        if self.delta is None:
            # futures delta per contract_size or notional
            self.delta = FixedIncomeFuturesHedge.calculate_futures_delta(contract_size=self.notional,
                                                                         futures_duration=self.duration)
        self.calculate_hedge_contracts()
        self.calculate_initial_hedge_cost()

        # now reset the delta of the hedge contract
        self.delta = FixedIncomeFuturesHedge.calculate_futures_delta(contract_size=self.notional,
                                                                     futures_duration=self.duration)

    def calculate_hedge_contracts(self):
        if self.trade_delta > self.min_hedge_delta:
            create_hedge = True
        else:
            create_hedge = False
        if create_hedge:
            if not self.trade_beta:
                raise ValueError("Futures Hedge calculation called on trade with no hedges set")
            self.hedge_contracts = np.round(self.trade_beta[self.sym] * self.trade_delta / self.delta)

    def calculate_initial_hedge_cost(self):
        if not self.trade_beta:
            raise ValueError("Futures Hedge calculation called on trade with no hedges set")
        self.notional *= self.hedge_contracts

    @staticmethod
    def calculate_futures_delta(contract_size, futures_duration):
        return futures_duration * contract_size * 0.0001

    def markout_mults(self):
        return {'price': (1 / self.par_value) * self.notional,
                'PV': self.delta,
                'cents': 100.0,
                'bps': (1.0 / self.duration / self.par_value) * 10000}


"""
Handle OTC related hedge calcs
"""


class FixedIncomeOTCHedge(Trade):
    def __init__(self, *args, **kwargs):
        # self.package_id = None
        self.min_hedge_delta = 1000  # in relevant ccy
        # self.trade = None
        self.duration = None  # <- hedge duration attribute for the time being
        self.trade_delta = None  # <- hedge trade_delta attribute for the time being
        self.trade_beta = dict()
        # self.settle_date = None
        self.package_size = None  # package_size of the trade executed
        self.leg_no = None  # -1 would be the package leg . 0/1/2/3 are the leg_Nos
        self.price_type = None

        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        self.notional = 1  # for OTC bonds
        self.paper_trade = True
        self.hedge_contracts = 0.0
        self.par_value = 100
        self.maturity_date = None
        self.adj_traded_px = self.traded_px

        # self.notional = 0.0
        # self.traded_px = None
        # set delta of hedge instrument
        if self.delta is None:
            # futures delta should always be passed in
            self.delta = self.duration * self.notional * 0.0001
        # self.package_id = self.trade.package_id
        self.calculate_hedge_contracts()
        self.calculate_initial_hedge_cost()

        # now reset the hedge delta
        self.delta = self.duration * self.notional * 0.0001

    def calculate_hedge_contracts(self):
        if self.trade_delta > self.min_hedge_delta:
            create_hedge = True
        else:
            create_hedge = False
        if create_hedge:
            if not self.trade_beta:
                raise ValueError("OTC Hedge calculation called on trade with no hedges set")
            self.hedge_contracts = self.trade_beta[self.sym] * self.trade_delta / self.delta

    def calculate_initial_hedge_cost(self):
        if not self.trade_beta:
            raise ValueError("Futures Hedge calculation called on trade with no hedges set")
        self.notional *= self.hedge_contracts

    def markout_mults(self):
        return {'price': (1 / self.par_value) * self.notional,
                'PV': self.delta,
                'cents': 100.0,
                'bps': (1.0 / self.duration / self.par_value) * 10000}


''' Interest Rate Swap product
Specific changes:
1. markout_mults - Since Swaps is yield based so no need to do price to yield conversion'''


class InterestRateSwap(FixedIncomeTrade):
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
