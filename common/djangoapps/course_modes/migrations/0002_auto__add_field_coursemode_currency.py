# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CourseMode.currency'
        db.add_column('course_modes_coursemode', 'currency',
                      self.gf('django.db.models.fields.CharField')(default='usd', max_length=8),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'CourseMode.currency'
        db.delete_column('course_modes_coursemode', 'currency')


    models = {
        'course_modes.coursemode': {
            'Meta': {'object_name': 'CourseMode'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_price': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'mode_display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mode_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'suggested_prices': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['course_modes']
