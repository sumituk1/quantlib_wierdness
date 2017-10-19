from mosaicsmartdata.core.fx import FXPricingContextGenerator
from mosaicsmartdata.common import qc_csv_helper
from mosaicsmartdata.core.quote import Quote
import csv, copy
import pickle, cloudpickle
from aiostreams import run
import aiostreams.operators as op
from mosaicsmartdata.core.markout import MarkoutCalculator
import logging
from mosaicsmartdata.core.curve_utils import construct_OIS_curve, discounting_factor, get_rate, Cache
import datetime

# prepare data
from datetime import timedelta
from random import shuffle



## prepare data
with open('../resources/fx/data.pickle', 'rb') as f:
        tiny_quote_dict = pickle.load(f)

# that one quote happens to have the wrong date
tiny_quote_dict['USDSWOIS='][0].timestamp -= timedelta(days=1)
tiny_quote_dict['USDSWOIS='][0].instrument.spot_settle_date -= timedelta(days=1)
tiny_quote_dict['USDSWOIS='][0].instrument.maturity_date -= timedelta(days=1)

tiny_quotes_list =[quotes for key, quotes in tiny_quote_dict.items()]


#print(tiny_quotes_list)
gbpsn = [q[0] for q in tiny_quotes_list if q[0].sym == 'GBPSN='][0]
tiny_quotes_list += [[gbpsn]]
my_quotes = [q[0] for q in tiny_quotes_list]

# create a pricing context with information from all the quotes
stream = my_quotes | op.flat_map(FXPricingContextGenerator()) > []
run(stream)
#pc = stream.sink[-1]

curve_data = copy.deepcopy(Cache().data)

## prepare data
with open('../resources/fx/weird_curve_data.pickle', 'wb') as f:
    pickle.dump(curve_data,f)

with open('../resources/fx/weird_curve_data.pickle', 'rb') as f:
    curve_data = pickle.load(f)

new_curves = {}
for item in curve_data:
    new_curves[item[3]] = construct_OIS_curve(*item)

# compare the implied price with the original price for each instrument, print the deviations
# for quote in tiny_quotes_list:
#     # if 'OIS' not in sym: #and 'TN' not in sym:
#     mid = quote[0].mid
#     instr = quote[0].instrument
#     est = instr.price(pc)
#     if abs(mid - est) > 1e-6:
#         print(quote[0].sym, mid, est, abs(mid - est),
#               quote[0].timestamp.date(),
#               instr.settle_date,
#               instr.maturity_date)

gbpsn = [q[0] for q in tiny_quotes_list if q[0].sym == 'GBPSW='][0]
# gbptn = [q[0] for q in tiny_quotes_list if q[0].sym == 'GBPSN='][0]
q= gbpsn

print(q)
instr =q.instrument
a1 = instr.settle_date
a2 = instr.maturity_date

#my_curve = pc.curve['USD']
my_curve = new_curves['USD']
gbp_curve = new_curves['GBP']

# Forward rates from both curves calculate fine
# Forward rate call with identical arguments returns identical result
print(get_rate(my_curve, a1, a2), discounting_factor(my_curve, a1, a2))
print(get_rate(my_curve, a1, a2), discounting_factor(my_curve, a1, a2))
print(get_rate(my_curve, a1, a2), discounting_factor(my_curve, a1, a2))
print(get_rate(gbp_curve, a1, a2), discounting_factor(gbp_curve, a1, a2))

#print(pc.fair_fwd_points_extended(instr.ccy, a1, a2))

# I'm constructing another curve, nothing to do with ours!
dummy_curve = construct_OIS_curve(my_curve.source_data)

# and the very same command now returns a different value, 1.1178 instead of 1.1163!
print(get_rate(my_curve, a1, a2), discounting_factor(my_curve, a1, a2))
# and this command now throws an error!
print(get_rate(gbp_curve, a1, a2), discounting_factor(gbp_curve, a1, a2))

#print(pc.fair_fwd_points_extended(instr.ccy, a1, a2))
