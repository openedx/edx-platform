"""Provides base Commentable model class"""
from lms.lib.comment_client import models
from lms.lib.comment_client import settings


class Commentable(models.Model):

    base_url = "{prefix}/commentables".format(prefix=settings.PREFIX)
    type = 'commentable'
