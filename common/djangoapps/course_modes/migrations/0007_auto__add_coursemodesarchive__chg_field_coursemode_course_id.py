# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseModesArchive'
        db.create_table('course_modes_coursemodesarchive', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('mode_slug', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('mode_display_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('min_price', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('suggested_prices', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(default='', max_length=255, blank=True)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='usd', max_length=8)),
            ('expiration_date', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('expiration_datetime', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('course_modes', ['CourseModesArchive'])


        # Changing field 'CourseMode.course_id'
        db.alter_column('course_modes_coursemode', 'course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255))

    def backwards(self, orm):
        # Deleting model 'CourseModesArchive'
        db.delete_table('course_modes_coursemodesarchive')


        # Changing field 'CourseMode.course_id'
        db.alter_column('course_modes_coursemode', 'course_id', self.gf('django.db.models.fields.CharField')(max_length=255))

    models = {
        'course_modes.coursemode': {
            'Meta': {'unique_together': "(('course_id', 'mode_slug', 'currency'),)", 'object_name': 'CourseMode'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '8'}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'expiration_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_price': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'mode_display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mode_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'suggested_prices': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        'course_modes.coursemodesarchive': {
            'Meta': {'object_name': 'CourseModesArchive'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '8'}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'expiration_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_price': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'mode_display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mode_slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'suggested_prices': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['course_modes']