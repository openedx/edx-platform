from django.db import models


class Microsite(models.Model):
    key = models.CharField(max_length=63, db_index=True)
    subdomain = models.CharField(max_length=127, db_index=True)
    values = models.TextField(null=False, blank=True)

    # TODO: must add a is_active flag

    def __str__( self):
      return self.key
