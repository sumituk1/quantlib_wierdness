class MarkoutBasketBuilder:
    def __init__(self):
        self.basket = []

    def __call__(self, msg):
        self.basket.append(msg)
        if msg.paper_trade:
            return []
        else:
            my_msg = self.basket
            self.basket = []
            return [my_msg]


def aggregate_markouts(hedge_markout_msgs):
    # extract the non -paper trade
    trade_mk_msg = [x for x in hedge_markout_msgs if not x.paper_trade][0]
    # mults = trade_mk_msg.trade.markout_mults()

    trade_mk_msg.hedged_cents = sum([x.price_markout * x.trade.markout_mults()['cents'] for x in hedge_markout_msgs])
    trade_mk_msg.hedged_price = sum([x.price_markout * x.trade.markout_mults()['price'] for x in hedge_markout_msgs])
    trade_mk_msg.hedged_bps = trade_mk_msg.price / trade_mk_msg.trade.delta
    return [trade_mk_msg]
