"""Provides base Commentable model class"""
from comment_client import models
from comment_client import settings


class Commentable(models.Model):

    base_url = "{prefix}/commentables".format(prefix=settings.PREFIX)
    type = 'commentable'
