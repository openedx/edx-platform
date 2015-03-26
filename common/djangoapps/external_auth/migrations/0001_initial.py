# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ExternalAuthMap'
        db.create_table('external_auth_externalauthmap', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('external_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('external_domain', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('external_credentials', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('external_email', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('external_name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, blank=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, null=True)),
            ('internal_password', self.gf('django.db.models.fields.CharField')(max_length=31, blank=True)),
            ('dtcreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('dtsignup', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('external_auth', ['ExternalAuthMap'])

        # Adding unique constraint on 'ExternalAuthMap', fields ['external_id', 'external_domain']
        db.create_unique('external_auth_externalauthmap', ['external_id', 'external_domain'])


    def backwards(self, orm):
        # Removing unique constraint on 'ExternalAuthMap', fields ['external_id', 'external_domain']
        db.delete_unique('external_auth_externalauthmap', ['external_id', 'external_domain'])

        # Deleting model 'ExternalAuthMap'
        db.delete_table('external_auth_externalauthmap')


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
        'external_auth.externalauthmap': {
            'Meta': {'unique_together': "(('external_id', 'external_domain'),)", 'object_name': 'ExternalAuthMap'},
            'dtcreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dtsignup': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'external_credentials': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'external_domain': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'external_email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'external_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'external_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal_password': ('django.db.models.fields.CharField', [], {'max_length': '31', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True'})
        }
    }

    complete_apps = ['external_auth']
