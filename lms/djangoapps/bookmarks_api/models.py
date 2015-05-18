
import json

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from xmodule_django.models import CourseKeyField, LocationKeyField


class Bookmark(models.Model):
    """
    Unit Bookmarks model.
    """
    user = models.ForeignKey(User)
    course_key = CourseKeyField(max_length=255, db_index=True)
    usage_key = LocationKeyField(max_length=255, db_index=True)
    display_name = models.CharField(max_length=255, default="", help_text="Display name of XBlock")
    _path = models.TextField(db_column='path', null=True, blank=True, help_text="JSON, breadcrumbs to the XBlock")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def path(self):
        """
        Jsonify the path
        """
        return json.loads(self._path)

    @path.setter
    def path(self, value):
        """
        Un-Jsonify the path
        """
        self._path = json.dumps(value)

    @classmethod
    def create(cls, bookmark_dict):
        """
        Create the bookmark object.
        """
        path = bookmark_dict.get('_path', list())

        if len(path) < 1:
            raise ValidationError('Bookmark must contain at least one path.')

        bookmark_dict['_path'] = json.dumps(path)

        bookmark, __ = cls.objects.get_or_create(**bookmark_dict)
        return bookmark
