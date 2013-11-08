# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        from datetime import datetime
        for course_mode in orm.CourseMode.objects.all():
            if course_mode.expiration_date is None:
                course_mode.expiration_datetime = None
                course_mode.save()
            else:
                course_mode.expiration_datetime = datetime.combine(course_mode.expiration_date, datetime.min.time())
                course_mode.save()

    def backwards(self, orm):
        for course_mode in orm.CourseMode.objects.all():
            course_mode.expiration_datetime = None
            course_mode.save()

    models = {
        'course_modes.coursemode': {
            'Meta': {'unique_together': "(('course_id', 'mode_slug', 'currency'),)", 'object_name': 'CourseMode'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '8'}),
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
    symmetrical = True
