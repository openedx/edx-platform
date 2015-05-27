"""
Database models for the LTI provider feature.

This app uses migrations. If you make changes to this model, be sure to create
an appropriate migration file and check it in at the same time as your model
changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms schemamigration lti_provider --auto "description" --settings=devstack
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
    consumer_name = models.CharField(max_length=255)
    consumer_key = models.CharField(max_length=32, unique=True, db_index=True)
    consumer_secret = models.CharField(max_length=32, unique=True)


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
