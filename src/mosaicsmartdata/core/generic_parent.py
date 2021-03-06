if False:
    pass


class GenericParent:
    def __init__(self, *args, **kwargs):
        if len(kwargs):
            raise ValueError('Unknown arguments:', kwargs)

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @staticmethod
    def split_kwargs(kwargs, goodargs):
        other_kwargs = {key: value for key, value in kwargs.items() if key not in goodargs}
        good_kwargs = {key: value for key, value in kwargs.items() if key in goodargs}
        return good_kwargs, other_kwargs

    def apply_kwargs(self, goodargs, kwargs):
        # print('Entering apply_kwargs', self, goodargs, kwargs)
        good_kwargs, other_kwargs = self.split_kwargs(kwargs, goodargs)
        for key, value in good_kwargs.items():
            self.__dict__[key] = value

        return other_kwargs

    def check_values(self, names):
        for x in names:
            if self.__dict__[x] is None:
                raise ValueError(x + ' must be specified')

    def __str__(self):
        my_string = str(type(self)) + ' : '
        for key, value in self.__dict__.items():
            my_string = my_string + ', ' + key + ' = ' + str(value)
        my_string = my_string.replace(': ,', ': ')
        return my_string