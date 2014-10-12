# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BaytPublishedCertificate'
        db.create_table('edraak_bayt_baytpublishedcertificate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('edraak_bayt', ['BaytPublishedCertificate'])


    def backwards(self, orm):
        # Deleting model 'BaytPublishedCertificate'
        db.delete_table('edraak_bayt_baytpublishedcertificate')


    models = {
        'edraak_bayt.baytpublishedcertificate': {
            'Meta': {'object_name': 'BaytPublishedCertificate'},
            'course_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['edraak_bayt']