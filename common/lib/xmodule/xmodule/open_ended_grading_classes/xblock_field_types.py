from xblock.core import Integer, Float


class StringyFloat(Float):
    """
    A model type that converts from string to floats when reading from json
    """

    def from_json(self, value):
        try:
            return float(value)
        except:
            return None

