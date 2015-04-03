from django.db import models


class LtiConsumer(models.Model):
    """
    Database model representing an LTI consumer. This model stores the consumer
    specific settings, such as the OAuth key/secret pair and any LTI fields
    that must be persisted.
    """
    key = models.CharField(max_length=32, unique=True, db_index=True)
    secret = models.CharField(max_length=32, unique=True)
