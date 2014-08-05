# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CourseMode.description'
        db.add_column('course_modes_coursemode', 'description',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)


        # Changing field 'CourseMode.course_id'
        db.alter_column('course_modes_coursemode', 'course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255))

    def backwards(self, orm):
        # Deleting field 'CourseMode.description'
        db.delete_column('course_modes_coursemode', 'description')


        # Changing field 'CourseMode.course_id'
        db.alter_column('course_modes_coursemode', 'course_id', self.gf('django.db.models.fields.CharField')(max_length=255))

    models = {
        'course_modes.coursemode': {
            'Meta': {'unique_together': "(('course_id', 'mode_slug', 'currency'),)", 'object_name': 'CourseMode'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '8'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'expiration_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_price': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'mode_display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mode_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'suggested_prices': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['course_modes']