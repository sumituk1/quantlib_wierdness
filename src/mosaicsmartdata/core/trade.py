import mosaicsmartdata.common.quantlib.bond.fixed_bond as bond
from mosaicsmartdata.common.quantlib.bond.bond_forward_price import govbond_cleanprice_from_forwardprice
from mosaicsmartdata.core.generic_parent import GenericParent
from mosaicsmartdata.core.instrument import FixedIncomeIRSwap, FixedIncomeBondFuture, FixedIncomeBond, FXForward, FXSwap
from mosaicsmartdata.core.repo_singleton import *
import logging, collections

class Package:
    def __init__(self, legs = [], timestamp = None):
        '''
        :param legs: list of trades contained in the package
        '''
        self.legs = []
        self.package_id = None
        self.append(legs)
        if timestamp:
            self.timestamp = timestamp
        else:
            try:
                self.timestamp = max([leg.timestamp for leg in legs])
            except:
                self.timestamp = None

    # add one or multiple trades to the package
    def append(self, trade):

        if isinstance(trade,collections.Iterable):
            for t in trade:
                self.append(t)
            return
        else:
            if self.package_id is None:
                self.package_id = trade.package_id
            if not(trade.package_id == self.package_id):
                if trade.package_id is not None:
                    logging.getLogger(__name__).warning("Resetting trade package ID",trade.package_id,
                                                        "to match package ID", self.package_id)
                trade.package_id = self.package_id

            trade.package = self
            self.legs.append(trade)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

class Trade(GenericParent):
    def __init__(self, *args, **kwargs):
        self.trade_id = None
        self.package_id = None
        self.source_trade_id = None  # for derived paper trades only
        self.package = None # reference to the mother package
        self.orig_package_size = None # the size passed from the feed
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
        if not 'instrument' in self.__dict__:
            self.instrument = None
        # if not 'sym' in self.__dict__:
        #     self.sym =  None

        #self.package_size = None  # package_size of the trade executed

        # just paste this magic line in to assign the kwargs
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        if self.adj_traded_px  is None:
            self.adj_traded_px = self.traded_px
        # use this syntax to require non-None values for certain fields
        self.check_values(['trade_id'])

        if self.package_id is None:
            self.package_id = self.trade_id

    def __eq__(self, other):
        # need to do it this way to avoid endless recursion from package to trade and back
        # TODO: what is a cleaner way of achieving that, that also checks for 'same' packages w/o endless recursion?
        return self.compare_except_package(other)

    def compare_except_package(self, other):
        return all([self.__dict__[key] == other.__dict__[key] for key in self.__dict__.keys() if key not in ['package']])

    def markout_mults(self):
        return {'price': 1, 'PV': self.delta}

    # price the trade was done at, using the price convention the user expects for markouts
    def traded_price(self):
        price = None
        try:
            price = self.adj_traded_px
        except:
            pass
        if not price:
            price = self.traded_px
        return price

    # price for the current trade given pricing data, using the price convention the user expects for markouts
    def valuation_price(self, pricing_context):
        return pricing_context # if it's a price for a discrete instrument, that's all we need

    def side_mult(self):
        if self.side == TradeSide.Ask:
            return -1
        else:
            return 1

    def price_diff(self, pricing_context):
        p_diff = self.valuation_price(pricing_context) - self.traded_price()
        p_diff *= self.side_mult()
        return p_diff

    def PV(self, pricing_context):
        # price the trade using
        return self.price_diff(pricing_context)*self.markout_mults['PV']


    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        # calculate different markout types on the fly by applying the correct multiplier
        elif item in self.instrument.__dict__:
            return self.instrument.__dict__[item]
        elif item in ['package_size']:
            if self.package is None:
                if self.orig_package_size is not None:
                    return self.orig_package_size
                else:
                    return 1
            else:
                return len(self.package.legs)
        else:
            raise AttributeError('This object doesn\'t have attribute' + item)

class FXTrade(Trade):
    pass

class FXForwardTrade(FXTrade):
    def __init__(self, instr: FXForward, **kwargs):
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))
        self.instrument = instr
        self.traded_px = abs(instr.notionals[1] / instr.notionals[0])
        # TODO: enter a proper analytical delta
        self.delta = 1.0

    # price for the current trade given pricing data, using the price convention the user expects for markouts
    def valuation_price(self, pricing_context):
        if type(pricing_context) == float or type(pricing_context) == int:
            return pricing_context  # if it's a price for a discrete instrument, that's all we need
        else: # assume it's a PricingContext
            # TODO: get a spot or forward rate, depending
            return pricing_context.spot_rate(self.instrument.ccy)


class FXSwapTrade(FXTrade):
    def __init__(self, instr: FXSwap, **kwargs):
        kwargs['instrument'] = instr # required arg
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
        # self.maturity_date = None
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
        if self.delta is None:
            # futures delta should always be passed in
            self.delta = self.duration * self.notional * 0.0001

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

    # price the trade was done at, using the price convention the user expects for markouts
    def traded_price(self):
        return -self.adj_traded_px # really?

    # price for the current trade given pricing data, using the price convention the user expects for markouts
    def valuation_price(self, pricing_context):
        return -pricing_context # if it's a price for a discrete instrument, that's all we need



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
