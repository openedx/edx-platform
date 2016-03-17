# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseAggregatedMetaData'
        db.create_table('course_metadata_courseaggregatedmetadata', (
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, primary_key=True, db_index=True)),
            ('total_modules', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('total_assessments', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('course_metadata', ['CourseAggregatedMetaData'])


    def backwards(self, orm):
        # Deleting model 'CourseAggregatedMetaData'
        db.delete_table('course_metadata_courseaggregatedmetadata')


    models = {
        'course_metadata.courseaggregatedmetadata': {
            'Meta': {'object_name': 'CourseAggregatedMetaData'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'primary_key': 'True', 'db_index': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'total_assessments': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_modules': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['course_metadata']