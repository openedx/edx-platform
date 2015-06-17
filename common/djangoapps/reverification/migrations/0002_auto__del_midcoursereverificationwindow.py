# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):


    def forwards(self, orm):
        # Deleting model 'MidcourseReverificationWindow'
        db.delete_table('reverification_midcoursereverificationwindow')


    def backwards(self, orm):
        # Adding model 'MidcourseReverificationWindow'
        db.create_table('reverification_midcoursereverificationwindow', (
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('reverification', ['MidcourseReverificationWindow'])


    models = {
        
    }

    complete_apps = ['reverification']
