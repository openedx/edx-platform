# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HistoricalMicrositeOrgMapping'
        db.create_table('microsite_configuration_historicalmicrositeorgmapping', (
            ('id', self.gf('django.db.models.fields.IntegerField')(db_index=True, blank=True)),
            ('org', self.gf('django.db.models.fields.CharField')(max_length=63, db_index=True)),
            ('microsite', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'+', null=True, on_delete=models.DO_NOTHING, to=orm['microsite_configuration.Microsite'])),
            (u'history_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            (u'history_date', self.gf('django.db.models.fields.DateTimeField')()),
            (u'history_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'+', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            (u'history_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('microsite_configuration', ['HistoricalMicrositeOrgMapping'])

        # Adding model 'MicrositeOrgMapping'
        db.create_table('microsite_configuration_micrositeorgmapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('org', self.gf('django.db.models.fields.CharField')(unique=True, max_length=63, db_index=True)),
            ('microsite', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['microsite_configuration.Microsite'])),
        ))
        db.send_create_signal('microsite_configuration', ['MicrositeOrgMapping'])


    def backwards(self, orm):
        # Deleting model 'HistoricalMicrositeOrgMapping'
        db.delete_table('microsite_configuration_historicalmicrositeorgmapping')

        # Deleting model 'MicrositeOrgMapping'
        db.delete_table('microsite_configuration_micrositeorgmapping')


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
        'microsite_configuration.historicalmicrositeorgmapping': {
            'Meta': {'ordering': "(u'-history_date', u'-history_id')", 'object_name': 'HistoricalMicrositeOrgMapping'},
            u'history_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'history_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            u'history_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            u'history_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'microsite': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'+'", 'null': 'True', 'on_delete': 'models.DO_NOTHING', 'to': "orm['microsite_configuration.Microsite']"}),
            'org': ('django.db.models.fields.CharField', [], {'max_length': '63', 'db_index': 'True'})
        },
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
        },
        'microsite_configuration.micrositeorgmapping': {
            'Meta': {'object_name': 'MicrositeOrgMapping'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'microsite': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['microsite_configuration.Microsite']"}),
            'org': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '63', 'db_index': 'True'})
        }
    }

    complete_apps = ['microsite_configuration']