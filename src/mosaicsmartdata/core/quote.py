from mosaicsmartdata.core.generic_parent import GenericParent


class Quote(GenericParent):
    def __init__(self, *args, **kwargs):
        self.sym = None
        self.timestamp = None  # <-- should be in datetime format
        self.bid = None
        self.ask = None
        self.duration = None  # <-- need this for hedging

        # just paste this magic line in to assign the kwargs
        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

        self.bid = float(self.bid)
        self.ask = float(self.ask)
        self.duration = float(self.duration) if self.duration is not None else None

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        # calculate different markout types on the fly by applying the correct multiplier
        elif str(item) == 'mid':
            return 0.5 * (self.bid + self.ask)
        else:
            if True: #str(item) not in ['__deepcopy__', '__getstate__']:
                raise AttributeError('This object doesn\'t have attribute \"' + item + '\"')

