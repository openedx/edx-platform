import uuid as uuid_tools

from django.conf import settings
from django.db import models

from model_utils.models import TimeStampedModel

class DigitalBook(TimeStampedModel):
    """
    Represents a digital book
    """

    def create_digital_book(cls, book_key):


#TODO: ceate a table to hold the list of digital books
#TODO: create a table that manages access to those digital books for specific users