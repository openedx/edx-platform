# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CmeUserProfile'
        db.create_table('cme_registration', (
            ('userprofile_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['student.UserProfile'], unique=True, primary_key=True)),
            ('profession', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('professional_designation', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('license_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('organization', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('stanford_affiliated', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('how_stanford_affiliated', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('patient_population', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True)),
            ('specialty', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('sub_specialty', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('address_1', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('address_2', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('state_province', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('extension', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('fax', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('hear_about_us', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('mailing_list', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('cme_registration', ['CmeUserProfile'])


    def backwards(self, orm):
        # Deleting model 'CmeUserProfile'
        db.delete_table('cme_registration')


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
        'cme_registration.cmeuserprofile': {
            'Meta': {'object_name': 'CmeUserProfile', 'db_table': "'cme_registration'", '_ormbases': ['student.UserProfile']},
            'address_1': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'address_2': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'extension': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'hear_about_us': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'how_stanford_affiliated': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'license_number': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'mailing_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'patient_population': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'profession': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'professional_designation': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'specialty': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'stanford_affiliated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state_province': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'sub_specialty': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'userprofile_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['student.UserProfile']", 'unique': 'True', 'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'student.userprofile': {
            'Meta': {'object_name': 'UserProfile', 'db_table': "'auth_userprofile'"},
            'allow_certificate': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'courseware': ('django.db.models.fields.CharField', [], {'default': "'course.xml'", 'max_length': '255', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'goals': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'level_of_education': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'mailing_address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'meta': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'year_of_birth': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['cme_registration']