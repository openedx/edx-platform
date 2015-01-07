# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'ProgressModules.course_id'
        db.alter_column('progress_modules', 'course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255))

    def backwards(self, orm):

        # Changing field 'ProgressModules.course_id'
        db.alter_column('progress_modules', 'course_id', self.gf('django.db.models.fields.CharField')(max_length=255))

    models = {
        'pgreport.progressmodules': {
            'Meta': {'object_name': 'ProgressModules', 'db_table': "'progress_modules'"},
            'correct_map': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'due': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'primary_key': 'True', 'db_index': 'True'}),
            'max_score': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'mean': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'median': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'module_type': ('django.db.models.fields.CharField', [], {'default': "'problem'", 'max_length': '255'}),
            'standard_deviation': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'student_answers': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'submit_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_score': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'variance': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'weight': ('django.db.models.fields.FloatField', [], {'null': 'True'})
        },
        'pgreport.progressmoduleshistory': {
            'Meta': {'ordering': "['-created', 'progress_module']", 'object_name': 'ProgressModulesHistory', 'db_table': "'progress_modules_history'"},
            'correct_map': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'due': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_score': ('django.db.models.fields.FloatField', [], {}),
            'mean': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'median': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'progress_module': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pgreport.ProgressModules']"}),
            'standard_deviation': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'student_answers': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'submit_count': ('django.db.models.fields.IntegerField', [], {}),
            'total_score': ('django.db.models.fields.FloatField', [], {}),
            'variance': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'weight': ('django.db.models.fields.FloatField', [], {'null': 'True'})
        }
    }

    complete_apps = ['pgreport']