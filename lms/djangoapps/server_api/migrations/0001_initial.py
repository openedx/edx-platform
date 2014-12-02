# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GroupRelationship'
        db.create_table('server_api_grouprelationship', (
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('group', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Group'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('parent_group', self.gf('django.db.models.fields.related.ForeignKey')(default=0, related_name='child_groups', null=True, blank=True, to=orm['server_api.GroupRelationship'])),
            ('record_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('server_api', ['GroupRelationship'])

        # Adding model 'LinkedGroupRelationship'
        db.create_table('server_api_linkedgrouprelationship', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('from_group_relationship', self.gf('django.db.models.fields.related.ForeignKey')(related_name='from_group_relationships', to=orm['server_api.GroupRelationship'])),
            ('to_group_relationship', self.gf('django.db.models.fields.related.ForeignKey')(related_name='to_group_relationships', to=orm['server_api.GroupRelationship'])),
            ('record_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('server_api', ['LinkedGroupRelationship'])

        # Adding model 'CourseGroupRelationship'
        db.create_table('server_api_coursegrouprelationship', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
            ('record_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('server_api', ['CourseGroupRelationship'])

        # Adding model 'GroupProfile'
        db.create_table('auth_groupprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('group', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Group'], unique=True)),
            ('group_type', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('record_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('server_api', ['GroupProfile'])

        # Adding model 'CourseContentGroupRelationship'
        db.create_table('server_api_coursecontentgrouprelationship', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('content_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('group_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['server_api.GroupProfile'])),
            ('record_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('server_api', ['CourseContentGroupRelationship'])

        # Adding unique constraint on 'CourseContentGroupRelationship', fields ['course_id', 'content_id', 'group_profile']
        db.create_unique('server_api_coursecontentgrouprelationship', ['course_id', 'content_id', 'group_profile_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'CourseContentGroupRelationship', fields ['course_id', 'content_id', 'group_profile']
        db.delete_unique('server_api_coursecontentgrouprelationship', ['course_id', 'content_id', 'group_profile_id'])

        # Deleting model 'GroupRelationship'
        db.delete_table('server_api_grouprelationship')

        # Deleting model 'LinkedGroupRelationship'
        db.delete_table('server_api_linkedgrouprelationship')

        # Deleting model 'CourseGroupRelationship'
        db.delete_table('server_api_coursegrouprelationship')

        # Deleting model 'GroupProfile'
        db.delete_table('auth_groupprofile')

        # Deleting model 'CourseContentGroupRelationship'
        db.delete_table('server_api_coursecontentgrouprelationship')


    models = {
        'server_api.coursecontentgrouprelationship': {
            'Meta': {'unique_together': "(('course_id', 'content_id', 'group_profile'),)", 'object_name': 'CourseContentGroupRelationship'},
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'group_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['server_api.GroupProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'server_api.coursegrouprelationship': {
            'Meta': {'object_name': 'CourseGroupRelationship'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'server_api.groupprofile': {
            'Meta': {'object_name': 'GroupProfile', 'db_table': "'auth_groupprofile'"},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True'}),
            'group_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'server_api.grouprelationship': {
            'Meta': {'object_name': 'GroupRelationship'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'group': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent_group': ('django.db.models.fields.related.ForeignKey', [], {'default': '0', 'related_name': "'child_groups'", 'null': 'True', 'blank': 'True', 'to': "orm['server_api.GroupRelationship']"}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'server_api.linkedgrouprelationship': {
            'Meta': {'object_name': 'LinkedGroupRelationship'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'from_group_relationship': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_group_relationships'", 'to': "orm['server_api.GroupRelationship']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'to_group_relationship': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_group_relationships'", 'to': "orm['server_api.GroupRelationship']"})
        },
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
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['server_api']
