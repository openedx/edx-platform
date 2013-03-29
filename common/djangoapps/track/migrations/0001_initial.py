# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TrackingLog'
        db.create_table('track_trackinglog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dtcreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('event_source', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('event_type', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('event', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('agent', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('page', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('track', ['TrackingLog'])


    def backwards(self, orm):
        # Deleting model 'TrackingLog'
        db.delete_table('track_trackinglog')


    models = {
        'track.trackinglog': {
            'Meta': {'object_name': 'TrackingLog'},
            'agent': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'dtcreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'event_source': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'page': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'})
        }
    }

    complete_apps = ['track']
