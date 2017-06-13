import numpy as np
from mosaicsmartdata.core.trade import InterestRateSwap, FixedIncomeTrade
from mosaicsmartdata.core.markout_msg import *

class MarkoutBasketBuilder:
    def __init__(self):
        self.basket = []

    def __call__(self, msg):
        self.basket.append(msg)
        if len(self.basket) >= msg.trade.package_size:
            my_msg = self.basket
            self.basket = []
            return [my_msg]
        else:
            return []

'''Calculates aggregated markouts for Unhedged trade and Hedge (paper-trade) belonging to a package'''
def aggregate_markouts(hedge_markout_msgs):
    # extract the non -paper trade
    trade_mk_msg = [x for x in hedge_markout_msgs if not x.paper_trade][0]

    ## for certain products like Swaps, cents markout is not applicable
    try:
        trade_mk_msg.hedged_cents = sum([x.price_markout * x.trade.markout_mults()['cents'] for x in hedge_markout_msgs])
    except Exception:
        pass

    try:
        for x in hedge_markout_msgs:
            if isinstance(x.trade, InterestRateSwap):
                trade_mk_msg.hedged_price = sum(filter(None,[trade_mk_msg.hedged_price,
                                                             x.price_markout * x.trade.markout_mults()['PV']]))
            else:
                trade_mk_msg.hedged_price = sum(filter(None,[trade_mk_msg.hedged_price,
                                                             x.price_markout * x.trade.markout_mults()['price']]))
        trade_mk_msg.hedged_bps = trade_mk_msg.hedged_price / trade_mk_msg.trade.delta
    except Exception:
        pass

    return trade_mk_msg

''' Aggregates the markouts of individual non-paper trades of a package'''
def aggregate_multi_leg_markouts(mkt_msgs):
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
    for x in mkt_msgs:
        if not x.trade.paper_trade:
            x.factor_PV_markout = mkmsg.factor_PV_markout
            x.factor_bps_markout = mkmsg.factor_bps_markout
            legs_count += 1
        if x.trade.paper_trade:
            hedge_legs_count += 1

    if legs_count == 1 and hedge_legs_count > 0:
        # for single leg Swaps, include the hedged markouts
        mkmsg = aggregate_markouts(mkt_msgs)
    else:
        # todo: handle higher order hedges!!
        mkmsg
    # mkmsg.price_markout = None
    # generate_package_mkt_msg(x.dt, net_PV)
    # mkmsg = MarkoutMessage2(trade=trade_lst,
    #                         # trade_id=mkt_msgs[0].trade.trade_id + "_PKG",
    #                         # notional=msg.notional,
    #                         # sym=msg.sym,
    #                         # side=msg.side,
    #                         factor_PV_markout=net_PV,
    #                         factor_bps_markout = net_PV/mkt_msgs[0].trade.factor_risk.total_factor_risk,
    #                         # next_timestamp=msg.timestamp + dt.timedelta(0, float(mk)),
    #                         dt=mkt_msgs[0].dt)
    return mkmsg