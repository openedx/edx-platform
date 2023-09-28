# pylint: disable=missing-docstring
"""Provides base Commentable model class"""


from openedx.core.djangoapps.django_comment_common.comment_client import models, settings


class Commentable(models.Model):

    accessible_fields = ['id', 'commentable_id']

    base_url = f"{settings.PREFIX}/commentables"
    type = 'commentable'

    def retrieve(self, *args, **kwargs):
        """
        Override default behavior because commentables don't actually exist in the comment service.
        """
        self.attributes["commentable_id"] = self.attributes["id"]
        self.retrieved = True
        return self
