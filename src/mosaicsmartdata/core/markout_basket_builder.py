import numpy as np
from mosaicsmartdata.core.trade import InterestRateSwapTrade, FixedIncomeTrade
from mosaicsmartdata.core.markout_msg import *

class MarkoutBasketBuilder:
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

    # Set up the DISLPAY_DV01
    if legs_count == 1 and hedge_legs_count > 0:
        # for single leg Swaps, include the hedged markouts
        mkmsg = aggregate_markouts(mkt_msgs)
        mkmsg.display_DV01 = mkt_msgs.trade.delta
    elif legs_count == 2 and hedge_legs_count == 0:
        # this is a multi-leg. Could be a 2 package rollover where factor risk doesn't work.

        # get the long leg
        if mkt_msgs[0].trade.maturity_date > mkt_msgs[1].trade.maturity_date:
            mkmsg.display_DV01 = np.abs(mkt_msgs[0].trade.duration - mkt_msgs[1].trade.duration) * \
                                 mkt_msgs[0].trade.delta * 0.0001
        else:
            mkmsg.display_DV01 = np.abs(mkt_msgs[0].trade.duration - mkt_msgs[1].trade.duration) * \
                                 mkt_msgs[1].trade.delta * 0.0001
    elif legs_count == 3 and hedge_legs_count == 0:
        # this is a multi-leg 3 legs.
        # set the display_DV01

        # get the belly leg
        if mkt_msgs[0].trade.maturity_date > mkt_msgs[1].trade.maturity_date > mkt_msgs[2].trade.maturity_date:
            mkmsg.display_DV01 = np.abs(mkt_msgs[0].trade.duration - mkt_msgs[1].trade.duration) * \
                                 mkt_msgs[0].trade.delta * 0.0001
        else:
            mkmsg.display_DV01 = np.abs(mkt_msgs[0].trade.duration - mkt_msgs[1].trade.duration) * \
                                 mkt_msgs[1].trade.delta * 0.0001

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