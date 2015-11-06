# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'CourseCompleteImageConfiguration'
        db.create_table('badges_coursecompleteimageconfiguration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mode', self.gf('django.db.models.fields.CharField')(unique=True, max_length=125)),
            ('icon', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('badges', ['CourseCompleteImageConfiguration'])

        db.create_table('badges_badgeclass', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(default=None, max_length=255, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=255)),
            ('issuing_component', self.gf('django.db.models.fields.SlugField')(default='', max_length=50, blank=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('criteria', self.gf('django.db.models.fields.TextField')()),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('mode', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('badges', ['BadgeClass'])

        # Adding model 'BadgeAssertion'
        db.create_table('badges_badgeassertion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('badge_class', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['badges.BadgeClass'])),
            ('backend', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('image_url', self.gf('django.db.models.fields.URLField')()),
            ('assertion_url', self.gf('django.db.models.fields.URLField')()),
            ('data', self.gf('jsonfield.fields.JSONField')()),
        ))
        db.send_create_signal('badges', ['BadgeAssertion'])

    def backwards(self, orm):

        # Deleting model 'BadgeAssertion'
        db.delete_table('badges_badgeassertion')

        # Deleting model 'BadgeClass'
        db.delete_table('badges_badgeclass')

        # Deleting model 'CourseCompleteImageConfiguration'
        db.delete_table('badges_coursecompleteimageconfiguration')

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
        'badges.badgeassertion': {
            'Meta': {'object_name': 'BadgeAssertion'},
            'data': ('jsonfield.fields.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'backend': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'badge_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['badges.BadgeClass']"}),
            'image_url': ('django.db.models.fields.URLField', [], {}),
            'assertion_url': ('django.db.models.fields.URLField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'badges.badgeclass': {
            'Meta': {'object_name': 'BadgeClass'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'default': 'None', 'max_length': '255', 'blank': 'True'}),
            'criteria': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'issuing_component': ('django.db.models.fields.SlugField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'max_length': '100', 'default': '""', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'})
        },
        'badges.coursecompleteimageconfiguration': {
            'Meta': {'object_name': 'CourseCompleteImageConfiguration'},
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '125'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['badges']