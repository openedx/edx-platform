import json

from django.db import models
from django.core.exceptions import ValidationError


def validate_json(values):
    try:
        json.loads(values)
    except ValueError, e:
        raise ValidationError("The values field must be a valid json.")


class Microsite(models.Model):
    key = models.CharField(max_length=63, db_index=True)
    subdomain = models.CharField(max_length=127, db_index=True)
    values = models.TextField(null=False, blank=True, validators=[validate_json])

    # TODO: an is_active flag would be useful

    def __str__( self):
      return self.key
