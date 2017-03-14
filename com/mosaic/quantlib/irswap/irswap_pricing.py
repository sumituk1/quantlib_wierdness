import QuantLib as ql
import pricing.Quantlib.curve.bootsrap as bt
calculation_date = ql.Date(20, 10, 2015)
ql.Settings.instance().evaluationDate = calculation_date

# construct discount curve and libor curve

risk_free_rate = 0.01
libor_rate = 0.02
day_count = ql.Actual365Fixed()

discount_curve = ql.YieldTermStructureHandle(ql.FlatForward(calculation_date, risk_free_rate, day_count))

libor_curve = ql.YieldTermStructureHandle(ql.FlatForward(calculation_date, libor_rate, day_count))

#libor3M_index = ql.Euribor3M(libor_curve)
libor3M_index = ql.USDLibor(ql.Period(3, ql.Months), libor_curve)

# Construct Swap
# We construct the fixed rate and floating rate leg schedules below.
calendar = ql.UnitedStates()
settle_date = calendar.advance(calculation_date, 5, ql.Days)
maturity_date = calendar.advance(settle_date, 10, ql.Years)

fixed_leg_tenor = ql.Period(6, ql.Months)
fixed_schedule = ql.Schedule(settle_date, maturity_date,
                             fixed_leg_tenor, calendar,
                             ql.ModifiedFollowing, ql.ModifiedFollowing,
                             ql.DateGeneration.Forward, False)

float_leg_tenor = ql.Period(3, ql.Months)
float_schedule = ql.Schedule (settle_date, maturity_date,
                              float_leg_tenor, calendar,
                              ql.ModifiedFollowing, ql.ModifiedFollowing,
                              ql.DateGeneration.Forward, False)
# construct a VanillaSwap
notional = 10000000
fixed_rate = 0.025
fixed_leg_daycount = ql.Actual360()
float_spread = 0.004
float_leg_daycount = ql.Actual360()

ir_swap = ql.VanillaSwap(ql.VanillaSwap.Payer, notional, fixed_schedule,
               fixed_rate, fixed_leg_daycount, float_schedule,
               libor3M_index, float_spread, float_leg_daycount )

# price the swap
swap_engine = ql.DiscountingSwapEngine(discount_curve)
ir_swap.setPricingEngine(swap_engine)

# get the fixed leg cashflows
for i, cf in enumerate(ir_swap.leg(0)):
    print ("%2d    %-18s  %10.2f"%(i+1, cf.date(), cf.amount()))

# get the floating leg cashflows
for i, cf in enumerate(ir_swap.leg(1)):
    print ("%2d    %-18s  %10.2f" % (i + 1, cf.date(), cf.amount()))

# Price the swap
print ("%-20s: %20.3f" % ("Net Present Value", ir_swap.NPV()))
print ("%-20s: %20.3f" % ("Fair Spread", ir_swap.fairSpread()))
print ("%-20s: %20.3f" % ("Fair Rate", ir_swap.fairRate()))
print ("%-20s: %20.3f" % ("Fixed Leg BPS", ir_swap.fixedLegBPS()))
print ("%-20s: %20.3f" % ("Floating Leg BPS", ir_swap.floatingLegBPS()))