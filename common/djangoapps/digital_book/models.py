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

    def get_or_create_digital_book_access(self, user, book_key):

        digital_book_access, created = self.objects.get_or_create(
            user=user,
            digital_book_key=book_key,
        )

        return digital_book_access, created