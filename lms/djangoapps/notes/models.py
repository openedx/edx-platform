from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
import json

from xmodule_django.models import CourseKeyField


class Note(models.Model):
    user = models.ForeignKey(User, db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True)
    uri = models.CharField(max_length=255, db_index=True)
    text = models.TextField(default="")
    quote = models.TextField(default="")
    range_start = models.CharField(max_length=2048)  # xpath string
    range_start_offset = models.IntegerField()
    range_end = models.CharField(max_length=2048)  # xpath string
    range_end_offset = models.IntegerField()
    tags = models.TextField(default="")  # comma-separated string
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)

    def clean(self, json_body):
        """
        Cleans the note object or raises a ValidationError.
        """
        if json_body is None:
            raise ValidationError('Note must have a body.')

        body = json.loads(json_body)
        if not isinstance(body, dict):
            raise ValidationError('Note body must be a dictionary.')

        # NOTE: all three of these fields should be considered user input
        # and may be output back to the user, so we need to sanitize them.
        # These fields should only contain _plain text_.
        self.uri = strip_tags(body.get('uri', ''))
        self.text = strip_tags(body.get('text', ''))
        self.quote = strip_tags(body.get('quote', ''))

        ranges = body.get('ranges')
        if ranges is None or len(ranges) != 1:
            raise ValidationError('Note must contain exactly one range.')

        self.range_start = ranges[0]['start']
        self.range_start_offset = ranges[0]['startOffset']
        self.range_end = ranges[0]['end']
        self.range_end_offset = ranges[0]['endOffset']

        self.tags = ""
        tags = [strip_tags(tag) for tag in body.get('tags', [])]
        if len(tags) > 0:
            self.tags = ",".join(tags)

    def get_absolute_url(self):
        """
        Returns the absolute url for the note object.
        """
        # pylint: disable=no-member
        kwargs = {'course_id': self.course_id.to_deprecated_string(), 'note_id': str(self.pk)}
        return reverse('notes_api_note', kwargs=kwargs)

    def as_dict(self):
        """
        Returns the note object as a dictionary.
        """
        return {
            'id': self.pk,
            'user_id': self.user.pk,
            'uri': self.uri,
            'text': self.text,
            'quote': self.quote,
            'ranges': [{
                'start': self.range_start,
                'startOffset': self.range_start_offset,
                'end': self.range_end,
                'endOffset': self.range_end_offset
            }],
            'tags': self.tags.split(","),
            'created': str(self.created),
            'updated': str(self.updated)
        }
