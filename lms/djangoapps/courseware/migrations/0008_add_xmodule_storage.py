# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'XModuleStudentInfoField'
        db.create_table('courseware_xmodulestudentinfofield', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('field_name', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('student', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('courseware', ['XModuleStudentInfoField'])

        # Adding unique constraint on 'XModuleStudentInfoField', fields ['student', 'field_name']
        db.create_unique('courseware_xmodulestudentinfofield', ['student_id', 'field_name'])

        # Adding model 'XModuleContentField'
        db.create_table('courseware_xmodulecontentfield', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('field_name', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('definition_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('courseware', ['XModuleContentField'])

        # Adding unique constraint on 'XModuleContentField', fields ['definition_id', 'field_name']
        db.create_unique('courseware_xmodulecontentfield', ['definition_id', 'field_name'])

        # Adding model 'XModuleSettingsField'
        db.create_table('courseware_xmodulesettingsfield', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('field_name', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('usage_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('courseware', ['XModuleSettingsField'])

        # Adding unique constraint on 'XModuleSettingsField', fields ['usage_id', 'field_name']
        db.create_unique('courseware_xmodulesettingsfield', ['usage_id', 'field_name'])

        # Adding model 'XModuleStudentPrefsField'
        db.create_table('courseware_xmodulestudentprefsfield', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('field_name', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('module_type', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('student', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('courseware', ['XModuleStudentPrefsField'])

        # Adding unique constraint on 'XModuleStudentPrefsField', fields ['student', 'module_type', 'field_name']
        db.create_unique('courseware_xmodulestudentprefsfield', ['student_id', 'module_type', 'field_name'])


    def backwards(self, orm):
        # Removing unique constraint on 'XModuleStudentPrefsField', fields ['student', 'module_type', 'field_name']
        db.delete_unique('courseware_xmodulestudentprefsfield', ['student_id', 'module_type', 'field_name'])

        # Removing unique constraint on 'XModuleSettingsField', fields ['usage_id', 'field_name']
        db.delete_unique('courseware_xmodulesettingsfield', ['usage_id', 'field_name'])

        # Removing unique constraint on 'XModuleContentField', fields ['definition_id', 'field_name']
        db.delete_unique('courseware_xmodulecontentfield', ['definition_id', 'field_name'])

        # Removing unique constraint on 'XModuleStudentInfoField', fields ['student', 'field_name']
        db.delete_unique('courseware_xmodulestudentinfofield', ['student_id', 'field_name'])

        # Deleting model 'XModuleStudentInfoField'
        db.delete_table('courseware_xmodulestudentinfofield')

        # Deleting model 'XModuleContentField'
        db.delete_table('courseware_xmodulecontentfield')

        # Deleting model 'XModuleSettingsField'
        db.delete_table('courseware_xmodulesettingsfield')

        # Deleting model 'XModuleStudentPrefsField'
        db.delete_table('courseware_xmodulestudentprefsfield')


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
        'courseware.xmodulecontentfield': {
            'Meta': {'unique_together': "(('definition_id', 'field_name'),)", 'object_name': 'XModuleContentField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'definition_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'courseware.xmodulesettingsfield': {
            'Meta': {'unique_together': "(('usage_id', 'field_name'),)", 'object_name': 'XModuleSettingsField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'usage_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'courseware.xmodulestudentinfofield': {
            'Meta': {'unique_together': "(('student', 'field_name'),)", 'object_name': 'XModuleStudentInfoField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'courseware.xmodulestudentprefsfield': {
            'Meta': {'unique_together': "(('student', 'module_type', 'field_name'),)", 'object_name': 'XModuleStudentPrefsField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'module_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['courseware']
