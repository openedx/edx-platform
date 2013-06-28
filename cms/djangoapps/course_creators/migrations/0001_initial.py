# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseCreators'
        db.create_table('course_creators_coursecreators', (
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64, primary_key=True)),
            ('state_changed', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='u', max_length=1)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=512, blank=True)),
        ))
        db.send_create_signal('course_creators', ['CourseCreators'])


    def backwards(self, orm):
        # Deleting model 'CourseCreators'
        db.delete_table('course_creators_coursecreators')


    models = {
        'course_creators.coursecreators': {
            'Meta': {'object_name': 'CourseCreators'},
            'note': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'u'", 'max_length': '1'}),
            'state_changed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'primary_key': 'True'})
        }
    }

    complete_apps = ['course_creators']