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


class DeletableByUserValue(object):
    """
    This mixin allows inheriting models to delete instances of the model
    associated with some specified user.
    """

    @classmethod
    def delete_by_user_value(cls, value, field):
        """
        Deletes instances of this model where ``field`` equals ``value``.

        e.g.
            ``delete_by_user_value(value='learner@example.com', field='email')``

        Returns True if any instances were deleted.
        Returns False otherwise.
        """
        filter_kwargs = {field: value}
        records_matching_user_value = cls.objects.filter(**filter_kwargs)

        if not records_matching_user_value.exists():
            return False

        records_matching_user_value.delete()
        return True
