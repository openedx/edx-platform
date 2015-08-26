"""
Database models for the LTI provider feature.
"""
from django.db import models
from django.dispatch import receiver

from courseware.models import SCORE_CHANGED


class LtiConsumer(models.Model):
    """
    Database model representing an LTI consumer. This model stores the consumer
    specific settings, such as the OAuth key/secret pair and any LTI fields
    that must be persisted.
    """
    key = models.CharField(max_length=32, unique=True, db_index=True)
    secret = models.CharField(max_length=32, unique=True)


@receiver(SCORE_CHANGED)
def score_changed_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume signals that indicate score changes.

    TODO: This function is a placeholder for integration with the LTI 1.1
    outcome service, which will follow in a separate change.
    """
    message = """LTI Provider got score change event:
        points_possible: {}
        points_earned: {}
        user_id: {}
        course_id: {}
        usage_id: {}
    """
    print message.format(
        kwargs.get('points_possible', None),
        kwargs.get('points_earned', None),
        kwargs.get('user_id', None),
        kwargs.get('course_id', None),
        kwargs.get('usage_id', None),
    )
