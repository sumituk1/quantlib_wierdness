# from django.db import models


# class CDS():
#     valuation_date
#     maturity_date
#     contract_spread
#     nominal
#     market_value
#     default_probability
#
#     term_structure_1m
#     term_structure_3m
#     term_structure_6m
#     term_structure_1y
#     term_structure_2y
#     term_structure_3y
#     term_structure_5y
#     term_structure_7y
#     term_structure_10y
#     term_structure_20y
#     term_structure_30y
#
#     result_npv
#     result_coupon_leg_bps
#     result_fair_spread
#     result_default_leg_npv
#     result_coupon_leg_npv
#     result_running_spread
#     result_implied_hazard_rate
#
#
#
# class IRS(models.Model):
#     valuation_date = models.DateField()
#     maturity_date = models.DateField()
#     start_date = models.DateField()
#
#     fixed_rate = models.FloatField()
#     spread = models.FloatField()
#
#     face = models.FloatField()
#
#     market_value = models.FloatField(null=True)
#     credit_spread = models.FloatField(null=True)
#
#     term_structure_1m = models.FloatField()
#     term_structure_3m = models.FloatField()
#     term_structure_6m = models.FloatField()
#     term_structure_1y = models.FloatField()
#     term_structure_2y = models.FloatField()
#     term_structure_3y = models.FloatField()
#     term_structure_5y = models.FloatField()
#     term_structure_7y = models.FloatField()
#     term_structure_10y = models.FloatField()
#     term_structure_20y = models.FloatField()
#     term_structure_30y = models.FloatField()
#
#     reference_index_term_structure_1m = models.FloatField()
#     reference_index_term_structure_3m = models.FloatField()
#     reference_index_term_structure_6m = models.FloatField()
#     reference_index_term_structure_1y = models.FloatField()
#     reference_index_term_structure_2y = models.FloatField()
#     reference_index_term_structure_3y = models.FloatField()
#     reference_index_term_structure_5y = models.FloatField()
#     reference_index_term_structure_7y = models.FloatField()
#     reference_index_term_structure_10y = models.FloatField()
#     reference_index_term_structure_20y = models.FloatField()
#     reference_index_term_structure_30y = models.FloatField()
#
#     fixed_leg_frequency_choice = (
#         ('once', 'Once'),
#         ('annual', 'Annual'),
#         ('semiannual', 'Semiannual'),
#         ('quarterly', 'Quarterly'),
#         ('bimonthly', 'Bimonthly'),
#         ('monthly', 'Monthly'),
#         ('weekly', 'Weekly'),
#         ('daily', 'Daily')
#     )
#
#     fixed_leg_frequency = models.CharField(max_length=10, choices=fixed_leg_frequency_choice)
#
#     floating_leg_frequency_choice = (
#         ('once', 'Once'),
#         ('annual', 'Annual'),
#         ('semiannual', 'Semiannual'),
#         ('quarterly', 'Quarterly'),
#         ('bimonthly', 'Bimonthly'),
#         ('monthly', 'Monthly'),
#         ('weekly', 'Weekly'),
#         ('daily', 'Daily')
#     )
#
#     floating_leg_frequency = models.CharField(max_length=10, choices=floating_leg_frequency_choice)
#
#     result_npv = models.FloatField(null=True)
#     result_fixed_leg_bps = models.FloatField(null=True)
#     result_floating_leg_bps = models.FloatField(null=True)
#     result_fair_rate = models.FloatField(null=True)
#     result_fair_spread = models.FloatField(null=True)
#
#     result_spread = models.FloatField(null=True)
#     result_duration = models.FloatField(null=True)
#     result_convexity = models.FloatField(null=True)
#     result_clean_price = models.FloatField(null=True)
#     result_bps = models.FloatField(null=True)
#     result_basis_pt_value = models.FloatField(null=True)
#     result_yield_value_bp = models.FloatField(null=True)
#
#     def sanity_check(self):  # use this to calc npv...
#         return self.val_date < self.expiry_date
#
#     def __unicode__(self):  # Python 3: def __str__(self):
#         return str(self.pk)
#
#
# class FRN(models.Model):
#     valuation_date = models.DateField()
#     maturity_date = models.DateField()
#     face = models.FloatField()
#
#     term_structure_1m = models.FloatField()
#     term_structure_3m = models.FloatField()
#     term_structure_6m = models.FloatField()
#     term_structure_1y = models.FloatField()
#     term_structure_2y = models.FloatField()
#     term_structure_3y = models.FloatField()
#     term_structure_5y = models.FloatField()
#     term_structure_7y = models.FloatField()
#     term_structure_10y = models.FloatField()
#     term_structure_20y = models.FloatField()
#     term_structure_30y = models.FloatField()
#
#     reference_index_term_structure_1m = models.FloatField()
#     reference_index_term_structure_3m = models.FloatField()
#     reference_index_term_structure_6m = models.FloatField()
#     reference_index_term_structure_1y = models.FloatField()
#     reference_index_term_structure_2y = models.FloatField()
#     reference_index_term_structure_3y = models.FloatField()
#     reference_index_term_structure_5y = models.FloatField()
#     reference_index_term_structure_7y = models.FloatField()
#     reference_index_term_structure_10y = models.FloatField()
#     reference_index_term_structure_20y = models.FloatField()
#     reference_index_term_structure_30y = models.FloatField()
#
#     payment_frequency_choice = (
#         ('once', 'Once'),
#         ('annual', 'Annual'),
#         ('semiannual', 'Semiannual'),
#         ('quarterly', 'Quarterly'),
#         ('bimonthly', 'Bimonthly'),
#         ('monthly', 'Monthly'),
#         ('weekly', 'Weekly'),
#         ('daily', 'Daily')
#     )
#
#     payment_frequency = models.CharField(max_length=10, choices=payment_frequency_choice)
#
#     current_floating_rate = models.FloatField(null=True)
#     spread = models.FloatField(null=True)
#
#     credit_spread = models.FloatField(null=True)
#     market_value = models.FloatField(null=True)
#
#     result_npv = models.FloatField(null=True)
#     result_clean_price = models.FloatField(null=True)
#     result_bps = models.FloatField(null=True)
#     result_basis_pt_value = models.FloatField(null=True)
#     result_yield_value_bp = models.FloatField(null=True)
#     result_spread = models.FloatField(null=True)
#     result_yield_to_maturity = models.FloatField(null=True)
#     result_accrued = models.FloatField(null=True)
#
#     def sanity_check(self):  # use this to calc npv...
#         return self.val_date < self.expiry_date
#
#     def __unicode__(self):  # Python 3: def __str__(self):
#         return str(self.pk)
#
#
# class Fixed_Rate_Bond(models.Model):
#     valuation_date = models.DateField()
#     maturity_date = models.DateField()
#     face = models.FloatField()
#
#     term_structure_1m = models.FloatField()
#     term_structure_3m = models.FloatField()
#     term_structure_6m = models.FloatField()
#     term_structure_1y = models.FloatField()
#     term_structure_2y = models.FloatField()
#     term_structure_3y = models.FloatField()
#     term_structure_5y = models.FloatField()
#     term_structure_7y = models.FloatField()
#     term_structure_10y = models.FloatField()
#     term_structure_20y = models.FloatField()
#     term_structure_30y = models.FloatField()
#
#     payment_frequency_choice = (('once', 'Once'),
#                                 ('annual', 'Annual'),
#                                 ('semiannual', 'Semiannual'),
#                                 ('quarterly', 'Quarterly'),
#                                 ('bimonthly', 'Bimonthly'),
#                                 ('monthly', 'Monthly'),
#                                 ('weekly', 'Weekly'),
#                                 ('daily', 'Daily')
#                                 )
#
#     payment_frequency = models.CharField(max_length=10, choices=payment_frequency_choice)
#
#     coupon = models.FloatField(null=True)
#
#     market_value = models.FloatField(null=True)
#     spread = models.FloatField(null=True)
#
#     result_npv = models.FloatField(null=True)
#     result_spread = models.FloatField(null=True)
#     result_duration = models.FloatField(null=True)
#     result_convexity = models.FloatField(null=True)
#
#     result_clean_price = models.FloatField(null=True)
#     result_bps = models.FloatField(null=True)
#     result_basis_pt_value = models.FloatField(null=True)
#     result_yield_value_bp = models.FloatField(null=True)
#
#     result_yield_to_maturity = models.FloatField(null=True)
#
#     result_accrued_amount = models.FloatField(null=True)
#
#     def sanity_check(self):  # use this to calc npv...
#         return self.val_date < self.expiry_date
#
#     def __unicode__(self):  # Python 3: def __str__(self):
#         return str(self.pk)