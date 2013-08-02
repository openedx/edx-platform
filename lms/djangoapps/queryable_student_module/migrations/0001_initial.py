# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StudentModuleExpand'
        db.create_table('queryable_studentmoduleexpand', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('student_module_id', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('attempts', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('module_type', self.gf('django.db.models.fields.CharField')(default='problem', max_length=32, db_index=True)),
            ('module_state_key', self.gf('django.db.models.fields.CharField')(max_length=255, db_column='module_id', db_index=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('student_id', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=30, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, null=True, blank=True)),
            ('grade', self.gf('django.db.models.fields.FloatField')(db_index=True, null=True, blank=True)),
            ('max_grade', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('queryable_student_module', ['StudentModuleExpand'])

        # Adding unique constraint on 'StudentModuleExpand', fields ['student_id', 'module_state_key', 'course_id']
        db.create_unique('queryable_studentmoduleexpand', ['student_id', 'module_id', 'course_id'])

        # Adding model 'CourseGrade'
        db.create_table('queryable_coursegrade', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('percent', self.gf('django.db.models.fields.FloatField')(null=True, db_index=True)),
            ('grade', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, db_index=True)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=30, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('queryable_student_module', ['CourseGrade'])

        # Adding unique constraint on 'CourseGrade', fields ['user_id', 'course_id']
        db.create_unique('queryable_coursegrade', ['user_id', 'course_id'])

        # Adding model 'AssignmentTypeGrade'
        db.create_table('queryable_assignmenttypegrade', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('percent', self.gf('django.db.models.fields.FloatField')(null=True, db_index=True)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=30, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('queryable_student_module', ['AssignmentTypeGrade'])

        # Adding unique constraint on 'AssignmentTypeGrade', fields ['user_id', 'course_id', 'category']
        db.create_unique('queryable_assignmenttypegrade', ['user_id', 'course_id', 'category'])

        # Adding model 'AssignmentGrade'
        db.create_table('queryable_assignmentgrade', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('percent', self.gf('django.db.models.fields.FloatField')(null=True, db_index=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('detail', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=30, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('queryable_student_module', ['AssignmentGrade'])

        # Adding unique constraint on 'AssignmentGrade', fields ['user_id', 'course_id', 'label']
        db.create_unique('queryable_assignmentgrade', ['user_id', 'course_id', 'label'])

        # Adding model 'Log'
        db.create_table('queryable_log', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('script_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
        ))
        db.send_create_signal('queryable_student_module', ['Log'])


    def backwards(self, orm):
        # Removing unique constraint on 'AssignmentGrade', fields ['user_id', 'course_id', 'label']
        db.delete_unique('queryable_assignmentgrade', ['user_id', 'course_id', 'label'])

        # Removing unique constraint on 'AssignmentTypeGrade', fields ['user_id', 'course_id', 'category']
        db.delete_unique('queryable_assignmenttypegrade', ['user_id', 'course_id', 'category'])

        # Removing unique constraint on 'CourseGrade', fields ['user_id', 'course_id']
        db.delete_unique('queryable_coursegrade', ['user_id', 'course_id'])

        # Removing unique constraint on 'StudentModuleExpand', fields ['student_id', 'module_state_key', 'course_id']
        db.delete_unique('queryable_studentmoduleexpand', ['student_id', 'module_id', 'course_id'])

        # Deleting model 'StudentModuleExpand'
        db.delete_table('queryable_studentmoduleexpand')

        # Deleting model 'CourseGrade'
        db.delete_table('queryable_coursegrade')

        # Deleting model 'AssignmentTypeGrade'
        db.delete_table('queryable_assignmenttypegrade')

        # Deleting model 'AssignmentGrade'
        db.delete_table('queryable_assignmentgrade')

        # Deleting model 'Log'
        db.delete_table('queryable_log')


    models = {
        'queryable_student_module.assignmentgrade': {
            'Meta': {'unique_together': "(('user_id', 'course_id', 'label'),)", 'object_name': 'AssignmentGrade', 'db_table': "'queryable_assignmentgrade'"},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'detail': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'percent': ('django.db.models.fields.FloatField', [], {'null': 'True', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'null': 'True', 'blank': 'True'})
        },
        'queryable_student_module.assignmenttypegrade': {
            'Meta': {'unique_together': "(('user_id', 'course_id', 'category'),)", 'object_name': 'AssignmentTypeGrade', 'db_table': "'queryable_assignmenttypegrade'"},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'percent': ('django.db.models.fields.FloatField', [], {'null': 'True', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'null': 'True', 'blank': 'True'})
        },
        'queryable_student_module.coursegrade': {
            'Meta': {'unique_together': "(('user_id', 'course_id'),)", 'object_name': 'CourseGrade', 'db_table': "'queryable_coursegrade'"},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'grade': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'percent': ('django.db.models.fields.FloatField', [], {'null': 'True', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'null': 'True', 'blank': 'True'})
        },
        'queryable_student_module.log': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Log', 'db_table': "'queryable_log'"},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'script_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'queryable_student_module.studentmoduleexpand': {
            'Meta': {'unique_together': "(('student_id', 'module_state_key', 'course_id'),)", 'object_name': 'StudentModuleExpand', 'db_table': "'queryable_studentmoduleexpand'"},
            'attempts': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'grade': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'max_grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'module_state_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_column': "'module_id'", 'db_index': 'True'}),
            'module_type': ('django.db.models.fields.CharField', [], {'default': "'problem'", 'max_length': '32', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'student_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'student_module_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['queryable_student_module']