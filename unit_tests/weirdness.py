
import pickle
from mosaicsmartdata.core.curve_utils import construct_OIS_curve, discounting_factor, get_rate
from datetime import date

with open('../resources/fx/weird_curve_data.pickle', 'rb') as f:
    curve_data = pickle.load(f)

new_curves = {}
for item in curve_data:
    new_curves[item[3]] = construct_OIS_curve(*item)

a1 = date(2017,6,28)
a2 = date(2017,7,5)

my_curve = new_curves['USD']
gbp_curve = new_curves['GBP']

print('Forward rates from both curves calculate fine')
print('Forward rate call with identical arguments returns identical result')
print(get_rate(my_curve, a1, a2), discounting_factor(my_curve, a1, a2))
print(get_rate(my_curve, a1, a2), discounting_factor(my_curve, a1, a2))
print(get_rate(gbp_curve, a1, a2), discounting_factor(gbp_curve, a1, a2))

#print(pc.fair_fwd_points_extended(instr.ccy, a1, a2))

print("Now let's construct another curve, nothing to do with ours!")
dummy_curve = construct_OIS_curve(my_curve.source_data)

print("and the very same command now returns a somewhat different value!")
print("(the difference in values was even larger in the non-toy example)")
print(get_rate(my_curve, a1, a2), discounting_factor(my_curve, a1, a2))
print("and the other forward rate command now throws an error!")
print(get_rate(gbp_curve, a1, a2), discounting_factor(gbp_curve, a1, a2))

#print(pc.fair_fwd_points_extended(instr.ccy, a1, a2))
