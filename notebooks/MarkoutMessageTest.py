# require at least Python 3.5 for async/await to work
from aiostreams import *
from mosaicsmartdata.core.trade import Quote, Trade, FixedIncomeTrade
from mosaicsmartdata.core.markout_msg import MarkoutMessage2

q=Quote(bid=1, ask = 2)
print(q.mid)

t = FixedIncomeTrade(trade_id =1, duration = 20, notional = 5)
msg = MarkoutMessage2(trade = t)
msg.price_markout = 1

print("price markout =%s, bps_markout=%s, cents_markout=%s, PV_markout=%s"%
      (msg.price_markout, msg.bps_markout, msg.cents_markout, msg.PV_markout))