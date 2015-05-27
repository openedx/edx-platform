# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseMode'
        db.create_table('course_modes_coursemode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('mode_slug', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('mode_display_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('min_price', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('suggested_prices', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(default='', max_length=255, blank=True)),
        ))
        db.send_create_signal('course_modes', ['CourseMode'])


    def backwards(self, orm):
        # Deleting model 'CourseMode'
        db.delete_table('course_modes_coursemode')


    models = {
        'course_modes.coursemode': {
            'Meta': {'object_name': 'CourseMode'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_price': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'mode_display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mode_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'suggested_prices': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['course_modes']
