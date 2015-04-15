# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, missing-docstring, unused-argument, unused-import, line-too-long

import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StudentFieldOverride'
        db.create_table('courseware_studentfieldoverride', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('location', self.gf('xmodule_django.models.LocationKeyField')(max_length=255, db_index=True)),
            ('student', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('field', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.TextField')(default='null')),
        ))
        db.send_create_signal('courseware', ['StudentFieldOverride'])

    def backwards(self, orm):
        # Deleting model 'StudentFieldOverride'
        db.delete_table('courseware_studentfieldoverride')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'courseware.offlinecomputedgrade': {
            'Meta': {'unique_together': "(('user', 'course_id'),)", 'object_name': 'OfflineComputedGrade'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'gradeset': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'courseware.offlinecomputedgradelog': {
            'Meta': {'ordering': "['-created']", 'object_name': 'OfflineComputedGradeLog'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nstudents': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'seconds': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'courseware.studentfieldoverride': {
            'Meta': {'unique_together': "(('course_id', 'location', 'student'),)", 'object_name': 'StudentFieldOverride'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        },
        'courseware.studentmodule': {
            'Meta': {'unique_together': "(('student', 'module_state_key', 'course_id'),)", 'object_name': 'StudentModule'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'done': ('django.db.models.fields.CharField', [], {'default': "'na'", 'max_length': '8', 'db_index': 'True'}),
            'grade': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'module_state_key': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_column': "'module_id'", 'db_index': 'True'}),
            'module_type': ('django.db.models.fields.CharField', [], {'default': "'problem'", 'max_length': '32', 'db_index': 'True'}),
            'state': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'courseware.studentmodulehistory': {
            'Meta': {'object_name': 'StudentModuleHistory'},
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'student_module': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['courseware.StudentModule']"}),
            'version': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'courseware.xmodulestudentinfofield': {
            'Meta': {'unique_together': "(('student', 'field_name'),)", 'object_name': 'XModuleStudentInfoField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        },
        'courseware.xmodulestudentprefsfield': {
            'Meta': {'unique_together': "(('student', 'module_type', 'field_name'),)", 'object_name': 'XModuleStudentPrefsField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'module_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        },
        'courseware.xmoduleuserstatesummaryfield': {
            'Meta': {'unique_together': "(('usage_id', 'field_name'),)", 'object_name': 'XModuleUserStateSummaryField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'usage_id': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        }
    }

    complete_apps = ['courseware']
