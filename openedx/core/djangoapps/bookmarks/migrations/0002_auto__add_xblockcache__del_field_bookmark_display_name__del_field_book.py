# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'XBlockCache'
        db.create_table('bookmarks_xblockcache', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('course_key', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('usage_key', self.gf('xmodule_django.models.LocationKeyField')(unique=True, max_length=255, db_index=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
            ('_paths', self.gf('jsonfield.fields.JSONField')(default=[], db_column='paths')),
        ))
        db.send_create_signal('bookmarks', ['XBlockCache'])

        # Deleting field 'Bookmark.display_name'
        db.delete_column('bookmarks_bookmark', 'display_name')

        # Deleting field 'Bookmark.path'
        db.delete_column('bookmarks_bookmark', 'path')

        # Adding field 'Bookmark._path'
        db.add_column('bookmarks_bookmark', '_path',
                      self.gf('jsonfield.fields.JSONField')(default='', db_column='path'),
                      keep_default=False)

        # Adding field 'Bookmark.xblock_cache'
        db.add_column('bookmarks_bookmark', 'xblock_cache',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['bookmarks.XBlockCache']),
                      keep_default=False)

        # Adding unique constraint on 'Bookmark', fields ['user', 'usage_key']
        db.create_unique('bookmarks_bookmark', ['user_id', 'usage_key'])


    def backwards(self, orm):
        # Removing unique constraint on 'Bookmark', fields ['user', 'usage_key']
        db.delete_unique('bookmarks_bookmark', ['user_id', 'usage_key'])

        # Deleting model 'XBlockCache'
        db.delete_table('bookmarks_xblockcache')

        # Adding field 'Bookmark.display_name'
        db.add_column('bookmarks_bookmark', 'display_name',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255),
                      keep_default=False)

        # Adding field 'Bookmark.path'
        db.add_column('bookmarks_bookmark', 'path',
                      self.gf('jsonfield.fields.JSONField')(default=''),
                      keep_default=False)

        # Deleting field 'Bookmark._path'
        db.delete_column('bookmarks_bookmark', 'path')

        # Deleting field 'Bookmark.xblock_cache'
        db.delete_column('bookmarks_bookmark', 'xblock_cache_id')


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
        'bookmarks.bookmark': {
            'Meta': {'unique_together': "(('user', 'usage_key'),)", 'object_name': 'Bookmark'},
            '_path': ('jsonfield.fields.JSONField', [], {'db_column': "'path'"}),
            'course_key': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'usage_key': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'xblock_cache': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bookmarks.XBlockCache']"})
        },
        'bookmarks.xblockcache': {
            'Meta': {'object_name': 'XBlockCache'},
            '_paths': ('jsonfield.fields.JSONField', [], {'default': '[]', 'db_column': "'paths'"}),
            'course_key': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'display_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'usage_key': ('xmodule_django.models.LocationKeyField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['bookmarks']