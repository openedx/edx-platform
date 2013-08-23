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
            ('student_module', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['courseware.StudentModule'])),
            ('attempts', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('module_type', self.gf('django.db.models.fields.CharField')(default='problem', max_length=32, db_index=True)),
            ('module_state_key', self.gf('django.db.models.fields.CharField')(max_length=255, db_column='module_id', db_index=True)),
            ('student', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('grade', self.gf('django.db.models.fields.FloatField')(db_index=True, null=True, blank=True)),
            ('max_grade', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('queryable', ['StudentModuleExpand'])

        # Adding unique constraint on 'StudentModuleExpand', fields ['student', 'module_state_key', 'course_id']
        db.create_unique('queryable_studentmoduleexpand', ['student_id', 'module_id', 'course_id'])

        # Adding model 'CourseGrade'
        db.create_table('queryable_coursegrade', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('percent', self.gf('django.db.models.fields.FloatField')(null=True, db_index=True)),
            ('grade', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('queryable', ['CourseGrade'])

        # Adding unique constraint on 'CourseGrade', fields ['user', 'course_id']
        db.create_unique('queryable_coursegrade', ['user_id', 'course_id'])

        # Adding model 'AssignmentTypeGrade'
        db.create_table('queryable_assignmenttypegrade', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('percent', self.gf('django.db.models.fields.FloatField')(null=True, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('queryable', ['AssignmentTypeGrade'])

        # Adding unique constraint on 'AssignmentTypeGrade', fields ['user', 'course_id', 'category']
        db.create_unique('queryable_assignmenttypegrade', ['user_id', 'course_id', 'category'])

        # Adding model 'AssignmentGrade'
        db.create_table('queryable_assignmentgrade', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('percent', self.gf('django.db.models.fields.FloatField')(null=True, db_index=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('detail', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('queryable', ['AssignmentGrade'])

        # Adding unique constraint on 'AssignmentGrade', fields ['user', 'course_id', 'label']
        db.create_unique('queryable_assignmentgrade', ['user_id', 'course_id', 'label'])

        # Adding model 'Log'
        db.create_table('queryable_log', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('script_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
        ))
        db.send_create_signal('queryable', ['Log'])


    def backwards(self, orm):
        # Removing unique constraint on 'AssignmentGrade', fields ['user', 'course_id', 'label']
        db.delete_unique('queryable_assignmentgrade', ['user_id', 'course_id', 'label'])

        # Removing unique constraint on 'AssignmentTypeGrade', fields ['user', 'course_id', 'category']
        db.delete_unique('queryable_assignmenttypegrade', ['user_id', 'course_id', 'category'])

        # Removing unique constraint on 'CourseGrade', fields ['user', 'course_id']
        db.delete_unique('queryable_coursegrade', ['user_id', 'course_id'])

        # Removing unique constraint on 'StudentModuleExpand', fields ['student', 'module_state_key', 'course_id']
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
        'courseware.studentmodule': {
            'Meta': {'unique_together': "(('student', 'module_state_key', 'course_id'),)", 'object_name': 'StudentModule'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'done': ('django.db.models.fields.CharField', [], {'default': "'na'", 'max_length': '8', 'db_index': 'True'}),
            'grade': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'module_state_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_column': "'module_id'", 'db_index': 'True'}),
            'module_type': ('django.db.models.fields.CharField', [], {'default': "'problem'", 'max_length': '32', 'db_index': 'True'}),
            'state': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'queryable.assignmentgrade': {
            'Meta': {'unique_together': "(('user', 'course_id', 'label'),)", 'object_name': 'AssignmentGrade'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'detail': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'percent': ('django.db.models.fields.FloatField', [], {'null': 'True', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'queryable.assignmenttypegrade': {
            'Meta': {'unique_together': "(('user', 'course_id', 'category'),)", 'object_name': 'AssignmentTypeGrade'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'percent': ('django.db.models.fields.FloatField', [], {'null': 'True', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'queryable.coursegrade': {
            'Meta': {'unique_together': "(('user', 'course_id'),)", 'object_name': 'CourseGrade'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'grade': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'percent': ('django.db.models.fields.FloatField', [], {'null': 'True', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'queryable.log': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Log'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'script_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'queryable.studentmoduleexpand': {
            'Meta': {'unique_together': "(('student', 'module_state_key', 'course_id'),)", 'object_name': 'StudentModuleExpand'},
            'attempts': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'grade': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'module_state_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_column': "'module_id'", 'db_index': 'True'}),
            'module_type': ('django.db.models.fields.CharField', [], {'default': "'problem'", 'max_length': '32', 'db_index': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'student_module': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['courseware.StudentModule']"})
        }
    }

    complete_apps = ['queryable']