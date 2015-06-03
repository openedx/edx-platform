# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseTeam'
        db.create_table('teams_courseteam', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('team_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('topic_id', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('country', self.gf('django_countries.fields.CountryField')(max_length=2, blank=True)),
            ('language', self.gf('student.models.LanguageField')(max_length=16, blank=True)),
        ))
        db.send_create_signal('teams', ['CourseTeam'])

        # Adding model 'CourseTeamMembership'
        db.create_table('teams_courseteammembership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(related_name='membership', to=orm['teams.CourseTeam'])),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('teams', ['CourseTeamMembership'])

        # Adding unique constraint on 'CourseTeamMembership', fields ['user', 'team']
        db.create_unique('teams_courseteammembership', ['user_id', 'team_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'CourseTeamMembership', fields ['user', 'team']
        db.delete_unique('teams_courseteammembership', ['user_id', 'team_id'])

        # Deleting model 'CourseTeam'
        db.delete_table('teams_courseteam')

        # Deleting model 'CourseTeamMembership'
        db.delete_table('teams_courseteammembership')


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
        'teams.courseteam': {
            'Meta': {'object_name': 'CourseTeam'},
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2', 'blank': 'True'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'language': ('student.models.LanguageField', [], {'max_length': '16', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'team_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'topic_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'related_name': "'teams'", 'symmetrical': 'False', 'through': "orm['teams.CourseTeamMembership']", 'to': "orm['auth.User']"})
        },
        'teams.courseteammembership': {
            'Meta': {'unique_together': "(('user', 'team'),)", 'object_name': 'CourseTeamMembership'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'membership'", 'to': "orm['teams.CourseTeam']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['teams']