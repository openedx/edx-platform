# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Workgroup'
        db.create_table('projects_workgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('projects', ['Workgroup'])

        # Adding M2M table for field users on 'Workgroup'
        db.create_table('projects_workgroup_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workgroup', models.ForeignKey(orm['projects.workgroup'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('projects_workgroup_users', ['workgroup_id', 'user_id'])

        # Adding M2M table for field groups on 'Workgroup'
        db.create_table('projects_workgroup_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workgroup', models.ForeignKey(orm['projects.workgroup'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('projects_workgroup_groups', ['workgroup_id', 'group_id'])

        # Adding model 'Project'
        db.create_table('projects_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('projects', ['Project'])

        # Adding unique constraint on 'Project', fields ['course_id', 'content_id']
        db.create_unique('projects_project', ['course_id', 'content_id'])

        # Adding M2M table for field workgroups on 'Project'
        db.create_table('projects_project_workgroups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['projects.project'], null=False)),
            ('workgroup', models.ForeignKey(orm['projects.workgroup'], null=False))
        ))
        db.create_unique('projects_project_workgroups', ['project_id', 'workgroup_id'])

        # Adding model 'Submission'
        db.create_table('projects_submission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('workgroup', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['projects.Workgroup'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='projects', to=orm['projects.Project'])),
            ('document_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('document_url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('document_mime_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('projects', ['Submission'])

        # Adding model 'SubmissionReview'
        db.create_table('projects_submissionreview', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submission_reviews', to=orm['projects.Submission'])),
            ('reviewer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submission_reviews', to=orm['auth.User'])),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('projects', ['SubmissionReview'])

        # Adding model 'PeerReview'
        db.create_table('projects_peerreview', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='peer_reviewees', to=orm['auth.User'])),
            ('reviewer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='peer_reviewers', to=orm['auth.User'])),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('projects', ['PeerReview'])

    def backwards(self, orm):
        # Removing unique constraint on 'Project', fields ['course_id', 'content_id']
        db.delete_unique('projects_project', ['course_id', 'content_id'])

        # Deleting model 'Workgroup'
        db.delete_table('projects_workgroup')

        # Removing M2M table for field users on 'Workgroup'
        db.delete_table('projects_workgroup_users')

        # Removing M2M table for field groups on 'Workgroup'
        db.delete_table('projects_workgroup_groups')

        # Deleting model 'Project'
        db.delete_table('projects_project')

        # Removing M2M table for field workgroups on 'Project'
        db.delete_table('projects_project_workgroups')

        # Deleting model 'Submission'
        db.delete_table('projects_submission')

        # Deleting model 'SubmissionReview'
        db.delete_table('projects_submissionreview')

        # Deleting model 'PeerReview'
        db.delete_table('projects_peerreview')

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
        'projects.peerreview': {
            'Meta': {'object_name': 'PeerReview'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'peer_reviewers'", 'to': "orm['auth.User']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'peer_reviewees'", 'to': "orm['auth.User']"})
        },
        'projects.project': {
            'Meta': {'unique_together': "(('course_id', 'content_id'),)", 'object_name': 'Project'},
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'workgroups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projects'", 'symmetrical': 'False', 'to': "orm['projects.Workgroup']"})
        },
        'projects.submission': {
            'Meta': {'object_name': 'Submission'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'document_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'document_mime_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'document_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projects'", 'to': "orm['projects.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'workgroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['projects.Workgroup']"})
        },
        'projects.submissionreview': {
            'Meta': {'object_name': 'SubmissionReview'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submission_reviews'", 'to': "orm['auth.User']"}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submission_reviews'", 'to': "orm['projects.Submission']"})
        },
        'projects.workgroup': {
            'Meta': {'object_name': 'Workgroup'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'workgroups'", 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'workgroups'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['projects']
