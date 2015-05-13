import json
from django.db import models
from django.core.exceptions import ValidationError


class Bookmark(models.Model):
    """
    Unit Bookmarks model.
    """
    user_id = models.CharField(max_length=255, db_index=True, help_text="Anonymized user id, not course specific")
    course_id = models.CharField(max_length=255, db_index=True)
    usage_id = models.CharField(max_length=255, help_text="ID of XBlock where the text comes from")
    display_name = models.TextField(default="", help_text="Display name of XBlock")
    path = models.TextField(help_text="JSON, describes the location of XBlock")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def create(cls, bookmark_dict):
        """
        Create the bookmark object.
        """
        if not isinstance(bookmark_dict, dict):
            raise ValidationError('Bookmark must be a dictionary.')

        if len(bookmark_dict) == 0:
            raise ValidationError('Bookmark must have a body.')

        path = bookmark_dict.get('path', list())

        if len(path) < 1:
            raise ValidationError('Bookmark must contain at least one path.')

        bookmark_dict['path'] = json.dumps(path)
        bookmark_dict['user_id'] = bookmark_dict.pop('user', None)

        return cls(**bookmark_dict)

    def as_dict(self):
        """
        Returns the note object as a dictionary.
        """
        created = self.created.isoformat() if self.created else None
        updated = self.updated.isoformat() if self.updated else None

        return {
            'id': str(self.pk),
            'user': self.user_id,
            'course_id': self.course_id,
            'usage_id': self.usage_id,
            'display_name': self.display_name,
            'path': json.loads(self.path),
            'created': created,
            'updated': updated,
        }
