# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, missing-docstring, unused-argument, unused-import, line-too-long
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'OutcomeService'
        db.create_table('lti_provider_outcomeservice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lis_outcome_service_url', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('lti_consumer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lti_provider.LtiConsumer'])),
        ))
        db.send_create_signal('lti_provider', ['OutcomeService'])

        # Adding model 'GradedAssignment'
        db.create_table('lti_provider_gradedassignment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('course_key', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('usage_key', self.gf('xmodule_django.models.UsageKeyField')(max_length=255, db_index=True)),
            ('outcome_service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lti_provider.OutcomeService'])),
            ('lis_result_sourcedid', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('lti_provider', ['GradedAssignment'])

        # Adding unique constraint on 'GradedAssignment', fields ['outcome_service', 'lis_result_sourcedid']
        db.create_unique('lti_provider_gradedassignment', ['outcome_service_id', 'lis_result_sourcedid'])

        # Adding field 'LtiConsumer.instance_guid'
        db.add_column('lti_provider_lticonsumer', 'instance_guid',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True),
                      keep_default=False)

        # Adding unique constraint on 'LtiConsumer', fields ['consumer_name']
        db.create_unique('lti_provider_lticonsumer', ['consumer_name'])


    def backwards(self, orm):
        # Removing unique constraint on 'LtiConsumer', fields ['consumer_name']
        db.delete_unique('lti_provider_lticonsumer', ['consumer_name'])

        # Removing unique constraint on 'GradedAssignment', fields ['outcome_service', 'lis_result_sourcedid']
        db.delete_unique('lti_provider_gradedassignment', ['outcome_service_id', 'lis_result_sourcedid'])

        # Deleting model 'OutcomeService'
        db.delete_table('lti_provider_outcomeservice')

        # Deleting model 'GradedAssignment'
        db.delete_table('lti_provider_gradedassignment')

        # Deleting field 'LtiConsumer.instance_guid'
        db.delete_column('lti_provider_lticonsumer', 'instance_guid')


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
        'lti_provider.gradedassignment': {
            'Meta': {'unique_together': "(('outcome_service', 'lis_result_sourcedid'),)", 'object_name': 'GradedAssignment'},
            'course_key': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lis_result_sourcedid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'outcome_service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lti_provider.OutcomeService']"}),
            'usage_key': ('xmodule_django.models.UsageKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'lti_provider.lticonsumer': {
            'Meta': {'object_name': 'LtiConsumer'},
            'consumer_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'consumer_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'consumer_secret': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_guid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        'lti_provider.outcomeservice': {
            'Meta': {'object_name': 'OutcomeService'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lis_outcome_service_url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'lti_consumer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lti_provider.LtiConsumer']"})
        }
    }

    complete_apps = ['lti_provider']
