# TODO: should be a singleton, support reflation

class DiscountingService:
    def __init__(self, disc_type = 'USD_OIS'):
        pass
    def __call__(self,date, ccy):
        return 1.0 # placeholder for a proper discounting service
