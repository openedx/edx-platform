# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
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

        # Adding model 'Workgroup'
        db.create_table('projects_workgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='workgroups', to=orm['projects.Project'])),
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

        # Adding model 'WorkgroupReview'
        db.create_table('projects_workgroupreview', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('workgroup', self.gf('django.db.models.fields.related.ForeignKey')(related_name='workgroup_reviews', to=orm['projects.Workgroup'])),
            ('reviewer', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('projects', ['WorkgroupReview'])

        # Adding model 'WorkgroupSubmission'
        db.create_table('projects_workgroupsubmission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('workgroup', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['projects.Workgroup'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['auth.User'])),
            ('document_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('document_url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('document_mime_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('projects', ['WorkgroupSubmission'])

        # Adding model 'WorkgroupSubmissionReview'
        db.create_table('projects_workgroupsubmissionreview', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reviews', to=orm['projects.WorkgroupSubmission'])),
            ('reviewer', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('projects', ['WorkgroupSubmissionReview'])

        # Adding model 'WorkgroupPeerReview'
        db.create_table('projects_workgrouppeerreview', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('workgroup', self.gf('django.db.models.fields.related.ForeignKey')(related_name='peer_reviews', to=orm['projects.Workgroup'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='workgroup_peer_reviewees', to=orm['auth.User'])),
            ('reviewer', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('projects', ['WorkgroupPeerReview'])

    def backwards(self, orm):
        # Removing unique constraint on 'Project', fields ['course_id', 'content_id']
        db.delete_unique('projects_project', ['course_id', 'content_id'])

        # Deleting model 'Project'
        db.delete_table('projects_project')

        # Deleting model 'Workgroup'
        db.delete_table('projects_workgroup')

        # Removing M2M table for field users on 'Workgroup'
        db.delete_table('projects_workgroup_users')

        # Removing M2M table for field groups on 'Workgroup'
        db.delete_table('projects_workgroup_groups')

        # Deleting model 'WorkgroupReview'
        db.delete_table('projects_workgroupreview')

        # Deleting model 'WorkgroupSubmission'
        db.delete_table('projects_workgroupsubmission')

        # Deleting model 'WorkgroupSubmissionReview'
        db.delete_table('projects_workgroupsubmissionreview')

        # Deleting model 'WorkgroupPeerReview'
        db.delete_table('projects_workgrouppeerreview')

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
        'projects.project': {
            'Meta': {'unique_together': "(('course_id', 'content_id'),)", 'object_name': 'Project'},
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        'projects.workgroup': {
            'Meta': {'object_name': 'Workgroup'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'workgroups'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'workgroups'", 'to': "orm['projects.Project']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'workgroups'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"})
        },
        'projects.workgrouppeerreview': {
            'Meta': {'object_name': 'WorkgroupPeerReview'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
            'document_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'document_mime_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'document_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['auth.User']"}),
            'workgroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['projects.Workgroup']"})
        },
        'projects.workgroupsubmissionreview': {
            'Meta': {'object_name': 'WorkgroupSubmissionReview'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reviewer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'to': "orm['projects.WorkgroupSubmission']"})
        }
    }

    complete_apps = ['projects']
