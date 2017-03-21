# http://gouthamanbalaraman.com/blog/quantlib-basics.html

import QuantLib as ql
date = ql.Date(31, 3, 2015)
print("Original date: %s"%date)
# add a date
date2 = date +1
print("Adding a  day %s"%date2)
# add a month
date2 = date + ql.Period(1, ql.Months)
print("Adding a month: %s"%date2)

# add a week
date2 = date + ql.Period(1, ql.Weeks)
print("Adding a week: %s"%date2)
# logical operations
print(ql.Date(31, 3, 2015) > ql.Date(1, 3, 2015))

# CALENDAR schedules
date1 = ql.Date(26, 11, 2016)
date2 = ql.Date(26, 12, 2017)
tenor = ql.Period(ql.Monthly) # quarterly cashflows
calendar = ql.UnitedStates() # US holiday calendar
schedule = ql.Schedule(date1, date2, tenor, calendar, ql.Following,
                       ql.Following, ql.DateGeneration.Forward, False)
print("Cashflow date =%s"%list(schedule))

# ------------------  Interest Rate compounding ---------------------#
# The InterestRate class can be used to store the interest rate with
# the compounding type, day count and the frequency of compounding

annualRate = 0.05
dayCount = ql.ActualActual()
compoundType = ql.Compounded
frequency = ql.Annual # Frequency = annual
interestRate = ql.InterestRate(annualRate, dayCount, compoundType, frequency)

print("Compounded annually for 2 years:%s"%interestRate.compoundFactor(2.0))
print("Manual compounded annually for 2 years:%s"% ((1+annualRate)*(1+ annualRate)))

print("Disc factor:%s"%interestRate.discountFactor(2.0))
print("Manual disc factor:%s"%(1/interestRate.compoundFactor(2.0)))