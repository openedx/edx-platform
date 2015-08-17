# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, missing-docstring, unused-argument, unused-import, line-too-long
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CustomCourseForEdX'
        db.create_table('ccx_customcourseforedx', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('coach', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('ccx', ['CustomCourseForEdX'])

        # Adding model 'CcxMembership'
        db.create_table('ccx_ccxmembership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ccx', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ccx.CustomCourseForEdX'])),
            ('student', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('ccx', ['CcxMembership'])

        # Adding model 'CcxFutureMembership'
        db.create_table('ccx_ccxfuturemembership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ccx', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ccx.CustomCourseForEdX'])),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('auto_enroll', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('ccx', ['CcxFutureMembership'])

        # Adding model 'CcxFieldOverride'
        db.create_table('ccx_ccxfieldoverride', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ccx', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ccx.CustomCourseForEdX'])),
            ('location', self.gf('xmodule_django.models.LocationKeyField')(max_length=255, db_index=True)),
            ('field', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.TextField')(default='null')),
        ))
        db.send_create_signal('ccx', ['CcxFieldOverride'])

        # Adding unique constraint on 'CcxFieldOverride', fields ['ccx', 'location', 'field']
        db.create_unique('ccx_ccxfieldoverride', ['ccx_id', 'location', 'field'])

    def backwards(self, orm):
        # Removing unique constraint on 'CcxFieldOverride', fields ['ccx', 'location', 'field']
        db.delete_unique('ccx_ccxfieldoverride', ['ccx_id', 'location', 'field'])

        # Deleting model 'CustomCourseForEdX'
        db.delete_table('ccx_customcourseforedx')

        # Deleting model 'CcxMembership'
        db.delete_table('ccx_ccxmembership')

        # Deleting model 'CcxFutureMembership'
        db.delete_table('ccx_ccxfuturemembership')

        # Deleting model 'CcxFieldOverride'
        db.delete_table('ccx_ccxfieldoverride')

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
        'ccx.ccxfieldoverride': {
            'Meta': {'unique_together': "(('ccx', 'location', 'field'),)", 'object_name': 'CcxFieldOverride'},
            'ccx': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ccx.CustomCourseForEdX']"}),
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        },
        'ccx.ccxfuturemembership': {
            'Meta': {'object_name': 'CcxFutureMembership'},
            'auto_enroll': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ccx': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ccx.CustomCourseForEdX']"}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'ccx.ccxmembership': {
            'Meta': {'object_name': 'CcxMembership'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ccx': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ccx.CustomCourseForEdX']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'ccx.customcourseforedx': {
            'Meta': {'object_name': 'CustomCourseForEdX'},
            'coach': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['ccx']
