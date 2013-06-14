# NOTE: this is for *test purposes only*. We need some sort of DB set
#       up for testing, but in dev/prod, whoever provisions ejabberd
#       should provision its auth database separately, *not* using
#       this migration data (as it's far from complete).
#
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'JabberUser'
        db.create_table(u'users', (
            ('username', self.gf('django.db.models.fields.CharField')(max_length=250, primary_key=True)),
            ('password', self.gf('django.db.models.fields.TextField')()),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'jabber', ['JabberUser'])


    def backwards(self, orm):
        # Deleting model 'JabberUser'
        db.delete_table(u'users')


    models = {
        u'jabber.jabberuser': {
            'Meta': {'object_name': 'JabberUser', 'db_table': "u'users'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.TextField', [], {}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '250', 'primary_key': 'True'})
        }
    }

    complete_apps = ['jabber']
