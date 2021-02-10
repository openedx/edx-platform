"""
Models to support persistence of NexBlock data.
"""
from django.db import models
from opaque_keys.edx.django.models import LearningContextKeyField


class NexBlockLearnerData(models.Model):
    """
    Unstructured JSON data associated with NexBlock type in a learning context.

    This model is the authoritative data store for learner data.
    It is written to by the Learner Event API and read from the Learner Data API.
    """

    # The learning context with which this data is associated.
    # ("learning context" is a more generic way of saying "course run")
    # Example: course-v1:edX+DemoX+1T2020
    learning_context_key = LearningContextKeyField(max_length=255)

    # The NexBlock type.
    # Example: @edx/nexblock-test-announcement
    block_type = models.CharField(max_length=255)

    # A JSON blob of all learner data associated with this
    # (learning_context, block_type) pair.
    value = models.TextField()

    class Meta:
        unique_together = ("learning_context_key", "block_type")
