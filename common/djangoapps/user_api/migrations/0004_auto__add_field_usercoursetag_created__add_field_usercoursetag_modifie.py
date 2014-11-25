# -*- coding: utf-8 -*-
from contextlib import contextmanager
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    @contextmanager
    def lock_table(self, table_name):
        """ Context manager for locking a table (MySQL only) """
        # Lock tables only under MySQL (it isn't supported for SQLLite)
        is_mysql = (db.backend_name == 'mysql')

        # Before the block executes, lock the specified table
        if is_mysql:
            db.execute("LOCK TABLE {table} WRITE".format(table=table_name))

        # Execute the block
        yield

        # Add a deferred statement to unlock tables
        # This will ensure that tables stay locked until
        # all deferred SQL executes
        # (for example, creating foreign key constraints and adding indices)
        if is_mysql:
            db.add_deferred_sql("UNLOCK TABLES")

    def forwards(self, orm):

        with self.lock_table('user_api_usercoursetag'):
            # Adding field 'UserCourseTag.created'
            db.add_column('user_api_usercoursetag', 'created',
                          self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now),
                          keep_default=False)

            # Adding field 'UserCourseTag.modified'
            db.add_column('user_api_usercoursetag', 'modified',
                          self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now),
                          keep_default=False)

            # Changing field 'UserCourseTag.course_id'
            db.alter_column('user_api_usercoursetag', 'course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255))

    def backwards(self, orm):
        # Deleting field 'UserCourseTag.created'
        db.delete_column('user_api_usercoursetag', 'created')

        # Deleting field 'UserCourseTag.modified'
        db.delete_column('user_api_usercoursetag', 'modified')

        # Changing field 'UserCourseTag.course_id'
        db.alter_column('user_api_usercoursetag', 'course_id', self.gf('django.db.models.fields.CharField')(max_length=255))

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
        'user_api.usercoursetag': {
            'Meta': {'unique_together': "(('user', 'course_id', 'key'),)", 'object_name': 'UserCourseTag'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'user_api.userpreference': {
            'Meta': {'unique_together': "(('user', 'key'),)", 'object_name': 'UserPreference'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'preferences'", 'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['user_api']
