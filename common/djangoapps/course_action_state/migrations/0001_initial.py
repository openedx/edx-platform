# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseRerunState'
        db.create_table('course_action_state_coursererunstate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_by_user+', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('updated_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='updated_by_user+', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('course_key', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('should_display', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('source_course_key', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('course_action_state', ['CourseRerunState'])

        # Adding unique constraint on 'CourseRerunState', fields ['course_key', 'action']
        db.create_unique('course_action_state_coursererunstate', ['course_key', 'action'])


    def backwards(self, orm):
        # Removing unique constraint on 'CourseRerunState', fields ['course_key', 'action']
        db.delete_unique('course_action_state_coursererunstate', ['course_key', 'action'])

        # Deleting model 'CourseRerunState'
        db.delete_table('course_action_state_coursererunstate')


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
        'course_action_state.coursererunstate': {
            'Meta': {'unique_together': "(('course_key', 'action'),)", 'object_name': 'CourseRerunState'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'course_key': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_by_user+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'should_display': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'source_course_key': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'updated_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'updated_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'updated_by_user+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['course_action_state']
