import uuid as uuid_tools

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from model_utils.models import TimeStampedModel


class DigitalBookAccess(TimeStampedModel):
    """
    Represent's a Student's Access to a given Digital Book
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    uuid = models.UUIDField(default=uuid_tools.uuid4, editable=False, unique=True)
    digital_book_key = models.CharField(max_length=200)

    @classmethod
    def get_or_create_digital_book_access(cls, username, book_key):

        user = User.objects.get(username=username)

        digital_book_access, created = cls.objects.get_or_create(
            user=user.id,
            digital_book_key=book_key,
        )

        return digital_book_access, created
