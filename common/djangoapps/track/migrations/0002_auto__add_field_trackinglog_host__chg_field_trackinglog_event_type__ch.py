# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'TrackingLog.host'
        db.add_column('track_trackinglog', 'host',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=64, blank=True),
                      keep_default=False)


        # Changing field 'TrackingLog.event_type'
        db.alter_column('track_trackinglog', 'event_type', self.gf('django.db.models.fields.CharField')(max_length=512))

        # Changing field 'TrackingLog.page'
        db.alter_column('track_trackinglog', 'page', self.gf('django.db.models.fields.CharField')(max_length=512, null=True))

    def backwards(self, orm):
        # Deleting field 'TrackingLog.host'
        db.delete_column('track_trackinglog', 'host')


        # Changing field 'TrackingLog.event_type'
        db.alter_column('track_trackinglog', 'event_type', self.gf('django.db.models.fields.CharField')(max_length=32))

        # Changing field 'TrackingLog.page'
        db.alter_column('track_trackinglog', 'page', self.gf('django.db.models.fields.CharField')(max_length=32, null=True))

    models = {
        'track.trackinglog': {
            'Meta': {'object_name': 'TrackingLog'},
            'agent': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'dtcreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'event_source': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'page': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'})
        }
    }

    complete_apps = ['track']
