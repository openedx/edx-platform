"""
Models to support persistence of NexBlock data.
"""

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class NexBlockInstance(models.Model):
    """
    An instance of a NeXBlock. Uniquely identified by UUID.

    This model is downstream of the NexWrapperBlock data stored with the course.
    Changes are pushed here upon course publish.
    """

    uuid = models.UUIDField(editable=False, unique=True)
    display_name = models.CharField(max_length=255)


class NexBlockInstanceDatum(models.Model):
    """
    An piece of data associated with a NeXBlock instance, keyed by a string.

    This model is downstream of the NexWrapperBlock data stored with the course.
    Changes are pushed here upon course publish.
    """

    instance = models.ForeignKey(
        to=NexBlockInstance, related_name="instance_data", on_delete=models.CASCADE
    )
    data_key = models.CharField(max_length=255)
    data_value = models.TextField()

    class Meta:
        unique_together = ("instance", "data_key")


class NexBlockInstanceLearnerDatum(models.Model):
    """
    An piece of data associated with a NeXBlock instance and learner, keyed by a string.

    This model is the authoritative data store for learner data.
    It is written to by the Learner Event API and read from the Learner Data API.
    """

    instance = models.ForeignKey(
        to=NexBlockInstance, related_name="learner_data", on_delete=models.CASCADE
    )
    # NULL learner indicates that the account was deleted or otherwise disassociated
    # with thie piece of learner data. We keep it in the table for now.
    # In a production release, we'd want to think about whether or not this data
    # would need to be permanently deleted since it might contain PII.
    learner = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    data_key = models.CharField(max_length=255)
    data_value = models.TextField()

    class Meta:
        unique_together = ("instance", "learner", "data_key")
