# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'CmeUserProfile.how_stanford_affiliated'
        db.delete_column('cme_registration', 'how_stanford_affiliated')

        # Deleting field 'CmeUserProfile.profession'
        db.delete_column('cme_registration', 'profession')

        # Deleting field 'CmeUserProfile.stanford_affiliated'
        db.delete_column('cme_registration', 'stanford_affiliated')

        # Deleting field 'CmeUserProfile.phone_number'
        db.delete_column('cme_registration', 'phone_number')

        # Deleting field 'CmeUserProfile.fax'
        db.delete_column('cme_registration', 'fax')

        # Deleting field 'CmeUserProfile.hear_about_us'
        db.delete_column('cme_registration', 'hear_about_us')

        # Deleting field 'CmeUserProfile.mailing_list'
        db.delete_column('cme_registration', 'mailing_list')

        # Deleting field 'CmeUserProfile.state_province'
        db.delete_column('cme_registration', 'state_province')

        # Deleting field 'CmeUserProfile.extension'
        db.delete_column('cme_registration', 'extension')

        # Deleting field 'CmeUserProfile.organization'
        db.delete_column('cme_registration', 'organization')

        # Adding field 'CmeUserProfile.first_name'
        db.add_column('cme_registration', 'first_name',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.last_name'
        db.add_column('cme_registration', 'last_name',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.middle_initial'
        db.add_column('cme_registration', 'middle_initial',
                      self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.birth_date'
        db.add_column('cme_registration', 'birth_date',
                      self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.license_country'
        db.add_column('cme_registration', 'license_country',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.license_state'
        db.add_column('cme_registration', 'license_state',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.physician_status'
        db.add_column('cme_registration', 'physician_status',
                      self.gf('django.db.models.fields.CharField')(max_length=8, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.affiliation'
        db.add_column('cme_registration', 'affiliation',
                      self.gf('django.db.models.fields.CharField')(max_length=46, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.other_affiliation'
        db.add_column('cme_registration', 'other_affiliation',
                      self.gf('django.db.models.fields.CharField')(max_length=46, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.sub_affiliation'
        db.add_column('cme_registration', 'sub_affiliation',
                      self.gf('django.db.models.fields.CharField')(max_length=46, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.stanford_department'
        db.add_column('cme_registration', 'stanford_department',
                      self.gf('django.db.models.fields.CharField')(max_length=46, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.sunet_id'
        db.add_column('cme_registration', 'sunet_id',
                      self.gf('django.db.models.fields.CharField')(max_length=33, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.state'
        db.add_column('cme_registration', 'state',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.county_province'
        db.add_column('cme_registration', 'county_province',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)


        # Changing field 'CmeUserProfile.license_number'
        db.alter_column('cme_registration', 'license_number', self.gf('django.db.models.fields.CharField')(max_length=20, null=True))

        # Changing field 'CmeUserProfile.professional_designation'
        db.alter_column('cme_registration', 'professional_designation', self.gf('django.db.models.fields.CharField')(max_length=25, null=True))

    def backwards(self, orm):
        # Adding field 'CmeUserProfile.how_stanford_affiliated'
        db.add_column('cme_registration', 'how_stanford_affiliated',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.profession'
        db.add_column('cme_registration', 'profession',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.stanford_affiliated'
        db.add_column('cme_registration', 'stanford_affiliated',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'CmeUserProfile.phone_number'
        db.add_column('cme_registration', 'phone_number',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.fax'
        db.add_column('cme_registration', 'fax',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.hear_about_us'
        db.add_column('cme_registration', 'hear_about_us',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.mailing_list'
        db.add_column('cme_registration', 'mailing_list',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'CmeUserProfile.state_province'
        db.add_column('cme_registration', 'state_province',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.extension'
        db.add_column('cme_registration', 'extension',
                      self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CmeUserProfile.organization'
        db.add_column('cme_registration', 'organization',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Deleting field 'CmeUserProfile.first_name'
        db.delete_column('cme_registration', 'first_name')

        # Deleting field 'CmeUserProfile.last_name'
        db.delete_column('cme_registration', 'last_name')

        # Deleting field 'CmeUserProfile.middle_initial'
        db.delete_column('cme_registration', 'middle_initial')

        # Deleting field 'CmeUserProfile.birth_date'
        db.delete_column('cme_registration', 'birth_date')

        # Deleting field 'CmeUserProfile.license_country'
        db.delete_column('cme_registration', 'license_country')

        # Deleting field 'CmeUserProfile.license_state'
        db.delete_column('cme_registration', 'license_state')

        # Deleting field 'CmeUserProfile.physician_status'
        db.delete_column('cme_registration', 'physician_status')

        # Deleting field 'CmeUserProfile.affiliation'
        db.delete_column('cme_registration', 'affiliation')

        # Deleting field 'CmeUserProfile.other_affiliation'
        db.delete_column('cme_registration', 'other_affiliation')

        # Deleting field 'CmeUserProfile.sub_affiliation'
        db.delete_column('cme_registration', 'sub_affiliation')

        # Deleting field 'CmeUserProfile.stanford_department'
        db.delete_column('cme_registration', 'stanford_department')

        # Deleting field 'CmeUserProfile.sunet_id'
        db.delete_column('cme_registration', 'sunet_id')

        # Deleting field 'CmeUserProfile.state'
        db.delete_column('cme_registration', 'state')

        # Deleting field 'CmeUserProfile.county_province'
        db.delete_column('cme_registration', 'county_province')


        # Changing field 'CmeUserProfile.license_number'
        db.alter_column('cme_registration', 'license_number', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'CmeUserProfile.professional_designation'
        db.alter_column('cme_registration', 'professional_designation', self.gf('django.db.models.fields.CharField')(max_length=3, null=True))

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
            'affiliation': ('django.db.models.fields.CharField', [], {'max_length': '46', 'null': 'True', 'blank': 'True'}),
            'birth_date': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'county_province': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'license_country': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'license_number': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'license_state': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'middle_initial': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'other_affiliation': ('django.db.models.fields.CharField', [], {'max_length': '46', 'null': 'True', 'blank': 'True'}),
            'patient_population': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'physician_status': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'professional_designation': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'specialty': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'stanford_department': ('django.db.models.fields.CharField', [], {'max_length': '46', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'sub_affiliation': ('django.db.models.fields.CharField', [], {'max_length': '46', 'null': 'True', 'blank': 'True'}),
            'sub_specialty': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'sunet_id': ('django.db.models.fields.CharField', [], {'max_length': '33', 'null': 'True', 'blank': 'True'}),
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