"""Provides base Commentable model class"""
import models
import settings

class Commentable(models.Model):

    base_url = "{prefix}/commentables".format(prefix=settings.PREFIX)
    type = 'commentable'
