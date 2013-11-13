# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AnonymousUserExpt'
        db.create_table('unauth_experiment_anonymoususerexpt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=64, null=True, blank=True)),
            ('user_agent', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('unauth_experiment', ['AnonymousUserExpt'])


    def backwards(self, orm):
        # Deleting model 'AnonymousUserExpt'
        db.delete_table('unauth_experiment_anonymoususerexpt')


    models = {
        'unauth_experiment.anonymoususerexpt': {
            'Meta': {'object_name': 'AnonymousUserExpt'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user_agent': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['unauth_experiment']