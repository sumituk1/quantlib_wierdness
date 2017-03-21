import numpy as np
import matplotlib.pyplot as plt
import QuantLib as ql

# For simplicity we will use an flat forward curve

# Set Evaluation Date
today = ql.Date(31,3,2015)
ql.Settings.instance().setEvaluationDate(today)
# Setup the yield termstructure
rate = ql.SimpleQuote(0.03)
rate_handle = ql.QuoteHandle(rate)
dc = ql.Actual365Fixed()
disc_curve = ql.FlatForward(today, rate_handle, dc)
disc_curve.enableExtrapolation()
hyts = ql.YieldTermStructureHandle(disc_curve)

# The yieldTermStructure object provides an method which gives us the
# discount factor for a particular date (QuantLib.Date object) or time
# in years (with 0 = evaluationDate). This method is called discount

discount = np.vectorize(hyts.discount)
tg = np.arange(0,10,1./12.)
plt.plot(tg, discount(tg))
plt.xlabel("time")
plt.ylabel("discount")
plt.title("Flat Forward Curve")
plt.show()
# In the next step we will setup up a plain vanilla EURIBOR 6M Swap with maturity in 10 years
# Therefore we generate an index and using the handle to our yield curve as forward curve and
# two schedules, one for the fixed rate leg with annual payments and one for the float leg with semi annual payments

start = ql.TARGET().advance(today, ql.Period("2D"))
end = ql.TARGET().advance(start, ql.Period( "10Y"))
nominal = 1e7
typ = ql.VanillaSwap.Payer
fixRate = 0.03
fixedLegTenor = ql.Period( "1y")
fixedLegBDC = ql.ModifiedFollowing
fixedLegDC = ql.Thirty360(ql.Thirty360.BondBasis)
index = ql.Euribor6M(ql.YieldTermStructureHandle(disc_curve))
spread = 0.0
fixedSchedule = ql.Schedule(start, end, fixedLegTenor, index.fixingCalendar(), fixedLegBDC, fixedLegBDC,
                            ql.DateGeneration.Backward, False)
floatSchedule = ql.Schedule(start, end, index.tenor(), index.fixingCalendar(), index.businessDayConvention(),
                            index.businessDayConvention(), ql.DateGeneration.Backward, False)
swap = ql.VanillaSwap(typ, nominal, fixedSchedule, fixRate, fixedLegDC, floatSchedule, index, spread,
                      index.dayCounter())

# The last step before we can calculate the NPV we need a pricing engine.
# We are going to use the discountingSwapEngine

# it will discount all future payments to the evaluation date and calculate
# the difference between the present values of the two legs.
engine = ql.DiscountingSwapEngine(ql.YieldTermStructureHandle(disc_curve))
swap.setPricingEngine(engine)

print("Swap NPV=%s"%swap.NPV())
print("Swap fair rate=%s"%swap.fairRate())