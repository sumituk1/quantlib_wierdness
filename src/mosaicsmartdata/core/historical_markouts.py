from mosaicsmartdata.core.markout import *
from mosaicsmartdata.core.pca_risk import *

def historical_pca_risk(trade_quote_list_tpl):
    pca_risk = PCARisk()
    trade, quote_list = trade_quote_list_tpl
    return [tuple((pca_risk(trade)[0],quote_list))]

def historical_markouts(trade_quote_list_tpl):
    trade_msg_relayed = False
    trade, quote_list = trade_quote_list_tpl
    govt_bond_markout_calculator = GovtBondMarkoutCalculator()
    mkt_msg_list = []
    # pca_risk = PCARisk()
    # govt_bond_markout_calculator(trade) ## call for the trade

    for quote in sorted(quote_list, key=lambda x: x.timestamp):
        if quote.timestamp < trade.timestamp and not trade_msg_relayed:
            mkt_msg_list += govt_bond_markout_calculator(quote)
        elif quote.timestamp >= trade.timestamp and not trade_msg_relayed:
            mkt_msg_list += govt_bond_markout_calculator(trade)
            trade_msg_relayed = True
            mkt_msg_list += govt_bond_markout_calculator(quote)
        elif trade_msg_relayed:
            mkt_msg_list += govt_bond_markout_calculator(quote)

    return mkt_msg_list

def historical_markouts_2(trade_quote_list_tpl):
    trade_msg_relayed = False
    trade_list, quote_list = trade_quote_list_tpl
    govt_bond_markout_calculator = GovtBondMarkoutCalculator()
    mkt_msg_list = []
    # pca_risk = PCARisk()
    # govt_bond_markout_calculator(trade) ## call for the trade

    for trade, quote in zip(*sorted(zip(trade_list, quote_list), key=lambda x: x.timestamp)):
        if quote.timestamp < trade.timestamp and not trade_msg_relayed:
            mkt_msg_list += govt_bond_markout_calculator(quote)
        elif quote.timestamp >= trade.timestamp and not trade_msg_relayed:
            mkt_msg_list += govt_bond_markout_calculator(trade)
            trade_msg_relayed = True
            mkt_msg_list += govt_bond_markout_calculator(quote)
        elif trade_msg_relayed:
            mkt_msg_list += govt_bond_markout_calculator(quote)

    return mkt_msg_list