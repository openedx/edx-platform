# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'MidcourseReverificationWindow.course_id'
        db.alter_column('reverification_midcoursereverificationwindow', 'course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255))

    def backwards(self, orm):

        # Changing field 'MidcourseReverificationWindow.course_id'
        db.alter_column('reverification_midcoursereverificationwindow', 'course_id', self.gf('django.db.models.fields.CharField')(max_length=255))

    models = {
        'reverification.midcoursereverificationwindow': {
            'Meta': {'object_name': 'MidcourseReverificationWindow'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['reverification']