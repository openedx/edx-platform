# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MicrositeHistory'
        db.create_table('microsite_configuration_micrositehistory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=63, db_index=True)),
            ('subdomain', self.gf('django.db.models.fields.CharField')(max_length=127, db_index=True)),
            ('values', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('microsite_configuration', ['MicrositeHistory'])

        # Adding unique constraint on 'Microsite', fields ['subdomain']
        db.create_unique('microsite_configuration_microsite', ['subdomain'])

        # Adding unique constraint on 'Microsite', fields ['key']
        db.create_unique('microsite_configuration_microsite', ['key'])


    def backwards(self, orm):
        # Removing unique constraint on 'Microsite', fields ['key']
        db.delete_unique('microsite_configuration_microsite', ['key'])

        # Removing unique constraint on 'Microsite', fields ['subdomain']
        db.delete_unique('microsite_configuration_microsite', ['subdomain'])

        # Deleting model 'MicrositeHistory'
        db.delete_table('microsite_configuration_micrositehistory')


    models = {
        'microsite_configuration.microsite': {
            'Meta': {'object_name': 'Microsite'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '63', 'db_index': 'True'}),
            'subdomain': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '127', 'db_index': 'True'}),
            'values': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'microsite_configuration.micrositehistory': {
            'Meta': {'object_name': 'MicrositeHistory'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '63', 'db_index': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'subdomain': ('django.db.models.fields.CharField', [], {'max_length': '127', 'db_index': 'True'}),
            'values': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['microsite_configuration']