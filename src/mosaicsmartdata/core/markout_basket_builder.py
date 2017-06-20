import numpy as np
from mosaicsmartdata.core.trade import InterestRateSwapTrade, FixedIncomeTrade
from mosaicsmartdata.core.markout_msg import *
from mosaicsmartdata.core.trade import Package
from mosaicsmartdata.core.markout_filter import *
import logging

tenor_tol = 1.0

class PackageBuilder:
    '''
    Collects all messages with the same basket_id
    '''
    def __init__(self):
        self.basket = []

    def __call__(self, msg):
        self.basket.append(msg)
        if len(self.basket) >= msg.trade.package_size:
            my_msg = self.basket
            self.basket = []
            out = Package(my_msg) # collect them in a Package object
            return [out]
        else:
            return []

class AllMarkoutFilter:
    def __init__(self):
        # filter_markout_state
        # True: do not transmit any of the mkt_msgs in a package
        # False: pass-through all the mkt messages
        self.filter_markout_state = True
        self.packages = []

    def __call__(self,pkg):
        self.packages.append(pkg)

        # if received the zero lag, do smart stuff
        if pkg.dt == '0':
            self.filter_markout_state = filter_markouts(pkg)
            # print("")

        if self.filter_markout_state:
            logging.info('Filtering markout messages for package_id: ' + pkg.package_id)
            return []
            # for p in self.packages:
            #     p = do_smart_filter(p, self.zero_markout_state)
            #
            # tmp = self.packages
            # self.packages = []
            # return tmp
        else:
            return self.packages



'''Calculates aggregated markouts for Unhedged trade and Hedge (paper-trade) belonging to a package'''
def aggregate_markouts(pkg):
    hedge_markout_msgs = pkg.legs
    # extract the non -paper trade
    trade_mk_msg = [x for x in hedge_markout_msgs if not x.paper_trade][0]

    ## for certain products like Swaps, cents markout is not applicable
    try:
        trade_mk_msg.hedged_cents = sum([x.price_markout * x.trade.markout_mults()['cents'] for x in hedge_markout_msgs])
    except Exception:
        pass

    try:
        for x in hedge_markout_msgs:
            if isinstance(x.trade, InterestRateSwapTrade):
                trade_mk_msg.hedged_price = sum(filter(None,[trade_mk_msg.hedged_price,
                                                             x.price_markout * x.trade.markout_mults()['PV']]))
            else:
                trade_mk_msg.hedged_price = sum(filter(None,[trade_mk_msg.hedged_price,
                                                             x.price_markout * x.trade.markout_mults()['price']]))
        trade_mk_msg.hedged_bps = trade_mk_msg.hedged_price / trade_mk_msg.trade.delta
    except Exception:
        pass

    return trade_mk_msg

''' 1. Aggregates the markouts of individual non-paper trades of a package
    2. Also calculates the display_DV01, to be used for:
        1) multi-legs for hitrate/per ratio weighting
        2) for short-term IMM rollovers (2 legs), where total_factor_risk doesn't work,
           this number should be used for Risk weighting'''

def aggregate_multi_leg_markouts(pkg):
    mkt_msgs = pkg.legs
    # 1. calculate the net $ PV
    net_PV = 0.0
    for x in mkt_msgs:
        net_PV += x.PV_markout
    trade_lst = []

    [trade_lst.append(x.trade) for x in mkt_msgs]
    mkmsg = mkt_msgs[0]

    # stamp the net_PV of the package on the new mkt_msg
    mkmsg.factor_PV_markout = net_PV

    # stamp the factor_bps_mo of the package on the new mkt_msg
    mkmsg.factor_bps_markout = net_PV/mkt_msgs[0].trade.factor_risk.total_factor_risk

    # mkmsg.is_package = True
    mkmsg.final_price = None
    mkmsg.next_timestamp = None
    mkmsg.initial_price = None
    legs_count = 0
    hedge_legs_count = 0

    # find out if the package is a multi-leg and if a hedge exists
    # for a hedge, need to calculate the hedged markout

    mkt_msgs.sort(key=lambda x: x.trade.instrument.maturity_date)

    for x in mkt_msgs:
        if not x.trade.paper_trade:
            x.factor_PV_markout = mkmsg.factor_PV_markout
            x.factor_bps_markout = mkmsg.factor_bps_markout
            legs_count += 1
        if x.trade.paper_trade:
            hedge_legs_count += 1
    mkmsg.nonpaper_legs_count = legs_count
    # Set up the DISLPAY_DV01
    if legs_count == 1 and hedge_legs_count > 0:
        # for single leg Swaps, include the hedged markouts
        mkmsg = aggregate_markouts(pkg)
        mkmsg.nonpaper_legs_count = legs_count
        # get the delta from the non-paper trade leg
        mkmsg.display_DV01 = [x.trade.delta for x in mkt_msgs if not x.trade.paper_trade]
    elif legs_count == 2 and hedge_legs_count == 0:
        # this is a multi-leg. Could be a 2 package rollover where factor risk doesn't work
        # OR a perfect paper hedge using cash

        # get the long leg
        # Assumes sorted in order of maturity asc
        mkmsg.display_DV01 = np.abs(mkt_msgs[1].trade.duration - mkt_msgs[0].trade.duration) * \
                             mkt_msgs[1].trade.notional * 0.0001

        if np.abs(mkt_msgs[0].trade.tenor - mkt_msgs[1].trade.tenor) < tenor_tol:
            # here factor risk wont work as this is a rollover over a short duration.
            # just take the display_DV01 and reset the total_factor_risk
            mkmsg.trade.factor_risk.total_factor_risk = mkmsg.display_DV01

    elif legs_count == 3 and hedge_legs_count == 0:
        # this is a multi-leg 3 legs.
        # set the display_DV01

        # get the belly leg
        mkmsg.display_DV01 = np.abs(2 * mkt_msgs[1].trade.duration - mkt_msgs[0].trade.duration -
                                    mkt_msgs[2].trade.duration) * mkt_msgs[1].trade.notional * 0.0001

    else:
        # todo: handle higher order hedges!!
        mkmsg

    return mkmsg