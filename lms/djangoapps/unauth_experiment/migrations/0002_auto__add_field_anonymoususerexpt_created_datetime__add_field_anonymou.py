# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'AnonymousUserExpt.created_datetime'
        db.add_column('unauth_experiment_anonymoususerexpt', 'created_datetime',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'AnonymousUserExpt.modified_datetime'
        db.add_column('unauth_experiment_anonymoususerexpt', 'modified_datetime',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'AnonymousUserExpt.created_datetime'
        db.delete_column('unauth_experiment_anonymoususerexpt', 'created_datetime')

        # Deleting field 'AnonymousUserExpt.modified_datetime'
        db.delete_column('unauth_experiment_anonymoususerexpt', 'modified_datetime')


    models = {
        'unauth_experiment.anonymoususerexpt': {
            'Meta': {'object_name': 'AnonymousUserExpt'},
            'created_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['unauth_experiment']