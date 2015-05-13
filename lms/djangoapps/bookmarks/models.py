"""
Models for Bookmarks.
"""

from django.contrib.auth.models import User
from django.db import models

from jsonfield.fields import JSONField
from model_utils.models import TimeStampedModel

from xmodule.modulestore.django import modulestore
from xmodule_django.models import CourseKeyField, LocationKeyField


class Bookmark(TimeStampedModel):
    """
    Bookmarks model.
    """
    user = models.ForeignKey(User, db_index=True)
    course_key = CourseKeyField(max_length=255, db_index=True)
    usage_key = LocationKeyField(max_length=255, db_index=True)
    display_name = models.CharField(max_length=255, default='', help_text='Display name of block')
    path = JSONField(help_text='Path in course tree to the block')

    @classmethod
    def create(cls, bookmark_data):
        """
        Create a Bookmark object.

        Arguments:
            bookmark_data (dict): The data to create the object with.

        Returns:
            A Bookmark object.

        Raises:
            ItemNotFoundError: If no block exists for the usage_key.
        """
        usage_key = bookmark_data.pop('usage_key')
        usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))

        block = modulestore().get_item(usage_key)

        bookmark_data['course_key'] = usage_key.course_key
        bookmark_data['display_name'] = block.display_name
        bookmark_data['path'] = cls.get_path(block)
        user = bookmark_data.pop('user')

        bookmark, __ = cls.objects.get_or_create(usage_key=usage_key, user=user, defaults=bookmark_data)
        return bookmark

    @staticmethod
    def get_path(block):
        """
        Returns data for the path to the block in the course tree.

        Arguments:
            block (XBlock): The block whose path is required.

        Returns:
            list of dicts of the form {'usage_id': <usage_id>, 'display_name': <display_name>}.
        """
        parent = block.get_parent()
        parents_data = []

        while parent is not None and parent.location.block_type not in ['course']:
            parents_data.append({"display_name": parent.display_name, "usage_id": unicode(parent.location)})
            parent = parent.get_parent()

        parents_data.reverse()
        return parents_data
