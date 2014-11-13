# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PersonalOnlineCourse'
        db.create_table('pocs_personalonlinecourse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('coach', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('pocs', ['PersonalOnlineCourse'])

        # Adding model 'PocMembership'
        db.create_table('pocs_pocmembership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('poc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pocs.PersonalOnlineCourse'])),
            ('student', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('pocs', ['PocMembership'])

        # Adding model 'PocFieldOverride'
        db.create_table('pocs_pocfieldoverride', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('poc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pocs.PersonalOnlineCourse'])),
            ('location', self.gf('xmodule_django.models.LocationKeyField')(max_length=255, db_index=True)),
            ('field', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.TextField')(default='null')),
        ))
        db.send_create_signal('pocs', ['PocFieldOverride'])

        # Adding unique constraint on 'PocFieldOverride', fields ['poc', 'location', 'field']
        db.create_unique('pocs_pocfieldoverride', ['poc_id', 'location', 'field'])


    def backwards(self, orm):
        # Removing unique constraint on 'PocFieldOverride', fields ['poc', 'location', 'field']
        db.delete_unique('pocs_pocfieldoverride', ['poc_id', 'location', 'field'])

        # Deleting model 'PersonalOnlineCourse'
        db.delete_table('pocs_personalonlinecourse')

        # Deleting model 'PocMembership'
        db.delete_table('pocs_pocmembership')

        # Deleting model 'PocFieldOverride'
        db.delete_table('pocs_pocfieldoverride')


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
        'pocs.personalonlinecourse': {
            'Meta': {'object_name': 'PersonalOnlineCourse'},
            'coach': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'pocs.pocfieldoverride': {
            'Meta': {'unique_together': "(('poc', 'location', 'field'),)", 'object_name': 'PocFieldOverride'},
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'poc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pocs.PersonalOnlineCourse']"}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        },
        'pocs.pocmembership': {
            'Meta': {'object_name': 'PocMembership'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pocs.PersonalOnlineCourse']"}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['pocs']