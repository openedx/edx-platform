# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseCreator'
        db.create_table('course_creators_coursecreator', (
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64, primary_key=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('state_changed', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='u', max_length=1)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=512, blank=True)),
        ))
        db.send_create_signal('course_creators', ['CourseCreator'])


    def backwards(self, orm):
        # Deleting model 'CourseCreator'
        db.delete_table('course_creators_coursecreator')


    models = {
        'course_creators.coursecreator': {
            'Meta': {'object_name': 'CourseCreator'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'u'", 'max_length': '1'}),
            'state_changed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'primary_key': 'True'})
        }
    }

    complete_apps = ['course_creators']