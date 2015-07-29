import json

from django.db import models
from django.core.exceptions import ValidationError


def validate_json(values):
    try:
        json.loads(values)
    except ValueError:
        raise ValidationError("The values field must be a valid json.")


class Microsite(models.Model):
    """
    This is where the information about the microsite gets stored to the db.
    To achieve the maximum flexibility, most of the fields are stored inside
    a json field.

    Notes:
        - The key field was required for the dict definition at the settings, and it
        is used in some of the microsite_configuration methods.
        - The subdomain is outside of the json so that it is posible to use a db query
        to improve performance.
        - The values field must be validated on save to prevent the platform from crashing
        badly in the case the string is not able to be loaded as json.
    """
    key = models.CharField(max_length=63, db_index=True)
    subdomain = models.CharField(max_length=127, db_index=True)
    values = models.TextField(null=False, blank=True, validators=[validate_json])

    def __str__(self):
        return self.key
