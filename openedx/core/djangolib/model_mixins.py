"""
Custom Django Model mixins.
"""


class DeprecatedModelMixin(object):
    """
    Used to make a class unusable in practice, but leave database tables intact.
    """
    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Override to kill usage of this model.
        """
        raise TypeError("This model has been deprecated and should not be used.")
