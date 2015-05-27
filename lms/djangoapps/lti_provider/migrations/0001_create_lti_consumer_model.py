# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, missing-docstring, unused-argument, unused-import, line-too-long
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LtiConsumer'
        db.create_table('lti_provider_lticonsumer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('consumer_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('consumer_key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32, db_index=True)),
            ('consumer_secret', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
        ))
        db.send_create_signal('lti_provider', ['LtiConsumer'])


    def backwards(self, orm):
        # Deleting model 'LtiConsumer'
        db.delete_table('lti_provider_lticonsumer')


    models = {
        'lti_provider.lticonsumer': {
            'Meta': {'object_name': 'LtiConsumer'},
            'consumer_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'consumer_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'consumer_secret': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['lti_provider']
