# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LtiUser'
        db.create_table('lti_provider_ltiuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lti_user_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
            ('edx_user_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('edx_password', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('lti_provider', ['LtiUser'])


    def backwards(self, orm):
        # Deleting model 'LtiUser'
        db.delete_table('lti_provider_ltiuser')


    models = {
        'lti_provider.lticonsumer': {
            'Meta': {'object_name': 'LtiConsumer'},
            'consumer_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'consumer_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'consumer_secret': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'lti_provider.ltiuser': {
            'Meta': {'object_name': 'LtiUser'},
            'edx_password': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'edx_user_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lti_user_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'})
        }
    }

    complete_apps = ['lti_provider']