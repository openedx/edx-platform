"""
Custom Django Model mixins.
"""

import logging
log = logging.getLogger(__name__)

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
        log.warning("LOOK: %s", str(cls.__mro__))
        delmeth = cls.objects.filter(**filter_kwargs).delete
        log.warning("LOOK: %s", delmeth)
        log.warning("im_self: %s", delmeth.im_self)
        log.warning("im_self.__class__: %s", delmeth.im_self.__class__)
        num_deleted_records, _ = delmeth()
        return num_deleted_records > 0
