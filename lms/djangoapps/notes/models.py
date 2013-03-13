from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

import json

class Note(models.Model):
    user = models.ForeignKey(User, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)
    body = models.TextField()

    def get_absolute_url(self):
        kwargs = {'course_id': self.course_id, 'note_id': str(self.id)}
        return reverse('notes_api_note', kwargs=kwargs)

    def as_dict(self):
        d = {}
        json_body = json.loads(self.body)
        if type(json_body) is dict:
            d.update(json_body)
        d['id'] = self.id
        return d