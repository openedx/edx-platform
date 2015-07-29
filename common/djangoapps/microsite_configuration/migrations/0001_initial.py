# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Microsite'
        db.create_table('microsite_configuration_microsite', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=63, db_index=True)),
            ('subdomain', self.gf('django.db.models.fields.CharField')(max_length=127, db_index=True)),
            ('values', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('microsite_configuration', ['Microsite'])


    def backwards(self, orm):
        # Deleting model 'Microsite'
        db.delete_table('microsite_configuration_microsite')


    models = {
        'microsite_configuration.microsite': {
            'Meta': {'object_name': 'Microsite'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '63', 'db_index': 'True'}),
            'subdomain': ('django.db.models.fields.CharField', [], {'max_length': '127', 'db_index': 'True'}),
            'values': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['microsite_configuration']