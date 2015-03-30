from django.db import models

class LtiConsumer(models.Model):
    key = models.CharField(max_length=32, unique=True, db_index=True)
    secret = models.CharField(max_length=32, unique=True)

    def __unicode__(self):
        return self.key + ":" + self.secret
