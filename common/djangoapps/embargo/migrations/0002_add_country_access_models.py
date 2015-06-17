# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Country'
        db.create_table('embargo_country', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country', self.gf('django_countries.fields.CountryField')(unique=True, max_length=2, db_index=True)),
        ))
        db.send_create_signal('embargo', ['Country'])

        # Adding model 'RestrictedCourse'
        db.create_table('embargo_restrictedcourse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_key', self.gf('xmodule_django.models.CourseKeyField')(unique=True, max_length=255, db_index=True)),
            ('enroll_msg_key', self.gf('django.db.models.fields.CharField')(default='default', max_length=255)),
            ('access_msg_key', self.gf('django.db.models.fields.CharField')(default='default', max_length=255)),
        ))
        db.send_create_signal('embargo', ['RestrictedCourse'])

        # Adding model 'CountryAccessRule'
        db.create_table('embargo_countryaccessrule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rule_type', self.gf('django.db.models.fields.CharField')(default='blacklist', max_length=255)),
            ('restricted_course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['embargo.RestrictedCourse'])),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['embargo.Country'])),
        ))
        db.send_create_signal('embargo', ['CountryAccessRule'])

        # Adding unique constraint on 'CountryAccessRule', fields ['restricted_course', 'country']
        db.create_unique('embargo_countryaccessrule', ['restricted_course_id', 'country_id'])


        # Changing field 'EmbargoedCourse.course_id'
        db.alter_column('embargo_embargoedcourse', 'course_id', self.gf('xmodule_django.models.CourseKeyField')(unique=True, max_length=255))

    def backwards(self, orm):
        # Removing unique constraint on 'CountryAccessRule', fields ['restricted_course', 'country']
        db.delete_unique('embargo_countryaccessrule', ['restricted_course_id', 'country_id'])

        # Deleting model 'Country'
        db.delete_table('embargo_country')

        # Deleting model 'RestrictedCourse'
        db.delete_table('embargo_restrictedcourse')

        # Deleting model 'CountryAccessRule'
        db.delete_table('embargo_countryaccessrule')


        # Changing field 'EmbargoedCourse.course_id'
        db.alter_column('embargo_embargoedcourse', 'course_id', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True))

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
        'embargo.country': {
            'Meta': {'ordering': "['country']", 'object_name': 'Country'},
            'country': ('django_countries.fields.CountryField', [], {'unique': 'True', 'max_length': '2', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'embargo.countryaccessrule': {
            'Meta': {'unique_together': "(('restricted_course', 'country'),)", 'object_name': 'CountryAccessRule'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['embargo.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restricted_course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['embargo.RestrictedCourse']"}),
            'rule_type': ('django.db.models.fields.CharField', [], {'default': "'blacklist'", 'max_length': '255'})
        },
        'embargo.embargoedcourse': {
            'Meta': {'object_name': 'EmbargoedCourse'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'embargoed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'embargo.embargoedstate': {
            'Meta': {'object_name': 'EmbargoedState'},
            'change_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'embargoed_countries': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'embargo.ipfilter': {
            'Meta': {'object_name': 'IPFilter'},
            'blacklist': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'change_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'whitelist': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'embargo.restrictedcourse': {
            'Meta': {'object_name': 'RestrictedCourse'},
            'access_msg_key': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '255'}),
            'course_key': ('xmodule_django.models.CourseKeyField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'enroll_msg_key': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['embargo']