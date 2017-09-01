def construct_OIS_curve(usd_ois_quotes):
    '''
    :param usd_ois_quotes: a dict where the key is the tuple (start date, end date) and the value is the quote
    :return: a curve object
    '''
    # TODO: implement
    pass


def get_rate(curve, start_date, end_date, **kwargs):
    '''
    :param curve:
    :param start_date:
    :param end_date:
    :param kwargs
    :return: a double: value of the rate implied by the curve between the two dates
    '''
    # TODO: implement
    pass


def discounting_factor(curve, start_date, end_date):
    '''
    Returns the discounting factor from the second date onto the first
    :param curve:
    :param start_date:
    :param end_date:
    :return: discounting factor
    '''
    pass


def curve_from_disc_factors(disc_factors, **kwargs):
    '''
    Constructs a discounting curve from a list of discount factors
    :param disc_factors: list of tuples (disc_factor, start_date, end_date)
    :param kwargs: Extra stuff like daycount conventions etc
    :return:
    '''
    pass