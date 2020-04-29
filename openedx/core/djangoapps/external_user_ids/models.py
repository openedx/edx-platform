"""
Models for External User Ids that are sent out of Open edX
"""

import uuid as uuid_tools
from logging import getLogger

from django.contrib.auth.models import User
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

LOGGER = getLogger(__name__)


class ExternalIdType(TimeStampedModel):
    """
    ExternalIdType defines the type (purpose, or expected use) of an external id. A user may have one id that is sent
    to Company A and another that is sent to Company B.

    .. no_pii:
    """
    MICROBACHELORS_COACHING = 'mb_coaching'
    LTI = 'lti'

    name = models.CharField(max_length=32, blank=False, unique=True, db_index=True)
    description = models.TextField()
    history = HistoricalRecords()

    class Meta:
        app_label = 'external_user_ids'

    def __str__(self):
        return self.name


class ExternalId(TimeStampedModel):
    """
    External ids are sent to systems or companies outside of Open edX. This allows us to limit the exposure of any
    given id.

    An external id is linked to an internal id, so that users may be re-identified if the external id is sent
    back to Open edX.

    .. no_pii: We store external_user_id here, but do not consider that PII under OEP-30.
    """
    external_user_id = models.UUIDField(default=uuid_tools.uuid4, editable=False, unique=True)
    external_id_type = models.ForeignKey(ExternalIdType, db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    history = HistoricalRecords()

    class Meta(object):
        unique_together = (('user', 'external_id_type'),)
        app_label = 'external_user_ids'

    @classmethod
    def user_has_external_id(cls, user, type_name):
        """
        Checks if a user has an ExternalId of the type_name provided
        Arguments:
            user: User to search for
            type_name (str): Name of the type of ExternalId
        Returns:
            (Bool): True if the user already has an external ID, False otherwise.
        """
        if not cls.objects.filter(
            user=user,
            external_id_type__name=type_name
        ).exists():
            return False
        return True

    @classmethod
    def add_new_user_id(cls, user, type_name):
        """
        Creates an ExternalId for the User of the type_name provided
        Arguments:
            user: User to create the ID for
            type_name (str): Name of the type of ExternalId
        Returns:
            (ExternalId): Returns the external id that was created or retrieved
            (Bool): True if the External ID was created, False if it already existed
        """
        try:
            type_obj = ExternalIdType.objects.get(name=type_name)
        except ExternalIdType.DoesNotExist:
            LOGGER.info(
                'External ID Creation failed for user {user}, no external id type of {type}'.format(
                    user=user.id,
                    type=type_name
                )
            )
            return None, False
        external_id, created = cls.objects.get_or_create(
            user=user,
            external_id_type=type_obj
        )
        if created:
            LOGGER.info(
                'External ID Created for user {user}, of type {type}'.format(
                    user=user.id,
                    type=type_name
                )
            )
        return external_id, created
