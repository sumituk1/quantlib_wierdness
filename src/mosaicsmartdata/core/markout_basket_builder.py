import numpy as np
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

'''Calculates aggregated markouts for Unhedged trade and Hedge (paper-trade)'''
def aggregate_markouts(hedge_markout_msgs):
    # extract the non -paper trade
    trade_mk_msg = [x for x in hedge_markout_msgs if not x.paper_trade][0]
    # mults = trade_mk_msg.trade.markout_mults()

    trade_mk_msg.hedged_cents = sum([x.price_markout * x.trade.markout_mults()['cents'] for x in hedge_markout_msgs])
    trade_mk_msg.hedged_price = sum([x.price_markout * x.trade.markout_mults()['price'] for x in hedge_markout_msgs])
    trade_mk_msg.hedged_bps = trade_mk_msg.hedged_price / trade_mk_msg.trade.delta
    return trade_mk_msg

''' Aggregates the markouts of individual non-paper trades '''
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
    if mkt_msgs.trade.package_size == 1:
        # include the hedged markouts
        aggregate_markouts(mkt_msgs)
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