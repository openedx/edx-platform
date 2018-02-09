import uuid as uuid_tools

from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel

class DigitalBookAccess(TimeStampedModel):
    """
    Represent's a Student's Access to a given Digital Book
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    uuid = models.UUIDField(default=uuid_tools.uuid4, editable=False, unique=True)
    digital_book_key = models.CharField(max_length=200)
