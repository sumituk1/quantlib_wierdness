import configparser


class ConfigParser(configparser.ConfigParser):
    """Can get options() without defaults
    """

    def options(self, section, no_defaults=False, **kwargs):
        if no_defaults:
            try:
                return self._sections[section]
            except KeyError:
                raise configparser.NoSectionError(section)
        else:
            return super().options(section, **kwargs)
