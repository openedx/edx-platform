
from django.db import models
from opaque_keys.edx.django.models import LearningContextKeyField, UsageKeyField


class ExternalDiscussionsIdMapping(models.Model):
    """
    Store a mapping from internal discussions context to external discussions context
    """
    context_key = LearningContextKeyField(max_length=255, db_index=True, null=False)
    usage_key = UsageKeyField(max_length=255, db_index=True, null=False)
    external_discussion_id = models.CharField(max_length=255, db_index=True, null=False)

    class Meta(object):
        constraints = [
            models.UniqueConstraint(
                fields=['context_key', 'usage_key'],
                name='unique_externaldiscussionsidmapping_context_usage')
        ]
        indexes = [
            models.Index(fields=['context_key', 'usage_key'])
        ]
