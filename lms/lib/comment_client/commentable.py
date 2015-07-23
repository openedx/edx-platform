"""Provides base Commentable model class"""
from lms.lib.comment_client import models
from lms.lib.comment_client import settings


class Commentable(models.Model):

    accessible_fields = ['id', 'commentable_id']

    base_url = "{prefix}/commentables".format(prefix=settings.PREFIX)
    type = 'commentable'
