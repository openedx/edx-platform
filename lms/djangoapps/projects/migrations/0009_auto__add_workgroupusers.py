# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # nothing to do. Simply added a WorkgroupUsers through table.
        pass


    def backwards(self, orm):
        # nothing to do. Simply added a WorkgroupUsers through table.
        pass

    models = {
        'api_manager.organization': {
            'Meta': {'object_name': 'Organization'},
            'contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'contact_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'contact_phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'workgroups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'symmetrical': 'False', 'to': "orm['projects.Workgroup']"})
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
        'projects.project': {
            'Meta': {'unique_together': "(('course_id', 'content_id', 'organization'),)", 'object_name': 'Project'},
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'projects'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['api_manager.Organization']"})
        },
        'projects.workgroup': {
            'Meta': {'object_name': 'Workgroup'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'workgroups'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'workgroups'", 'to': "orm['projects.Project']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'workgroups'", 'to': "orm['auth.User']", 'through': "orm['projects.WorkgroupUsers']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'})
        },
        'projects.workgrouppeerreview': {
            'Meta': {'object_name': 'WorkgroupPeerReview'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reviewer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'workgroup_peer_reviewees'", 'to': "orm['auth.User']"}),
            'workgroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'peer_reviews'", 'to': "orm['projects.Workgroup']"})
        },
        'projects.workgroupreview': {
            'Meta': {'object_name': 'WorkgroupReview'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reviewer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'workgroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'workgroup_reviews'", 'to': "orm['projects.Workgroup']"})
        },
        'projects.workgroupsubmission': {
            'Meta': {'object_name': 'WorkgroupSubmission'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'document_filename': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'document_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'document_mime_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'document_url': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['auth.User']"}),
            'workgroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['projects.Workgroup']"})
        },
        'projects.workgroupsubmissionreview': {
            'Meta': {'object_name': 'WorkgroupSubmissionReview'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reviewer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'to': "orm['projects.WorkgroupSubmission']"})
        },
        'projects.workgroupusers': {
            'Meta': {'object_name': 'WorkgroupUsers', 'db_table': "'projects_workgroup_users'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'workgroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Workgroup']"})
        }
    }

    complete_apps = ['projects']
