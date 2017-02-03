"""Provides base Commentable model class"""
from lms.lib.comment_client import models
from lms.lib.comment_client import settings


class Commentable(models.Model):

    accessible_fields = ['id', 'commentable_id']

    base_url = "{prefix}/commentables".format(prefix=settings.PREFIX)
    type = 'commentable'

    def retrieve(self, *args, **kwargs):
        """
        Override default behavior because commentables don't actually exist in the comment service.
        """
        self.attributes["commentable_id"] = self.attributes["id"]
        self.retrieved = True
        return self
