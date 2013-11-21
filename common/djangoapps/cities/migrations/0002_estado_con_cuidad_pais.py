# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'State'
        db.create_table('cities_state', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('country', self.gf('django_countries.fields.CountryField')(max_length=2)),
        ))
        db.send_create_signal('cities', ['State'])

        # Adding field 'City.state'
        db.add_column('cities_city', 'state',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cities.State'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'State'
        db.delete_table('cities_state')

        # Deleting field 'City.state'
        db.delete_column('cities_city', 'state_id')


    models = {
        'cities.city': {
            'Meta': {'object_name': 'City'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cities.State']", 'null': 'True', 'blank': 'True'})
        },
        'cities.state': {
            'Meta': {'object_name': 'State'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['cities']