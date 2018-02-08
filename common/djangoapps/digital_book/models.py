import uuid as uuid_tools

from django.conf import settings
from django.db import models

from model_utils.models import TimeStampedModel

class DigitalBookUserAccess(TimeStampedModel):
    """
    Represents a which users have access to which digital books
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    uuid = models.UUIDField(default=uuid_tools.uuid4, editable=False, unique=True)
    #TODO: set book key field to be a foreign key to a table that holds all digital books (will be similar to course runs table)
    book_key = models.CharField(max_length=100)
    order_number = models.CharField(max_length=128)
    #TODO: expired_at field should be present
    #TODO: policy field and policy table?


    def get_or_create_digital_book_user_access(cls, user, book_key, order_number):
        """
        creates a row in the table to represent an individual user's access
        to a specific book

        Arguments:
            user: User that has access to given book
            book_key: represents Digital book user has access to

        """
        # TODO: check inputs

        digital_book_access, created = cls.objects.get_or_create(
            user=user,
            book_key=book_key,
            order_number=order_number
        )

        return digital_book_access, created



