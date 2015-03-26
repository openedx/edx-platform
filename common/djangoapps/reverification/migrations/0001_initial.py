# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MidcourseReverificationWindow'
        db.create_table('reverification_midcoursereverificationwindow', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('reverification', ['MidcourseReverificationWindow'])


    def backwards(self, orm):
        # Deleting model 'MidcourseReverificationWindow'
        db.delete_table('reverification_midcoursereverificationwindow')


    models = {
        'reverification.midcoursereverificationwindow': {
            'Meta': {'object_name': 'MidcourseReverificationWindow'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['reverification']
