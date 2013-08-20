# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'UserProfile.qualification'
        db.delete_column('auth_userprofile', 'qualification')

        # Adding field 'UserProfile.lastname'
        db.add_column('auth_userprofile', 'lastname',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True, db_index=True),
                      keep_default=False)

        # Adding field 'UserProfile.firstname'
        db.add_column('auth_userprofile', 'firstname',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True, db_index=True),
                      keep_default=False)

        # Adding field 'UserProfile.middlename'
        db.add_column('auth_userprofile', 'middlename',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True, db_index=True),
                      keep_default=False)

        # Adding field 'UserProfile.education_place'
        db.add_column('auth_userprofile', 'education_place',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True),
                      keep_default=False)

        # Adding field 'UserProfile.education_year'
        db.add_column('auth_userprofile', 'education_year',
                      self.gf('django.db.models.fields.IntegerField')(null=True, db_index=True),
                      keep_default=False)

        # Adding field 'UserProfile.education_qualification'
        db.add_column('auth_userprofile', 'education_qualification',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfile.education_specialty'
        db.add_column('auth_userprofile', 'education_specialty',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_type'
        db.add_column('auth_userprofile', 'work_type',
                      self.gf('django.db.models.fields.CharField')(max_length=6, null=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_number'
        db.add_column('auth_userprofile', 'work_number',
                      self.gf('django.db.models.fields.IntegerField')(null=True, db_index=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_name'
        db.add_column('auth_userprofile', 'work_name',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_login'
        db.add_column('auth_userprofile', 'work_login',
                      self.gf('django.db.models.fields.CharField')(max_length=10, null=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_location'
        db.add_column('auth_userprofile', 'work_location',
                      self.gf('django.db.models.fields.CharField')(max_length=6, null=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_occupation'
        db.add_column('auth_userprofile', 'work_occupation',
                      self.gf('django.db.models.fields.CharField')(max_length=10, null=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_occupation_other'
        db.add_column('auth_userprofile', 'work_occupation_other',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=10, blank=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_teaching_experience'
        db.add_column('auth_userprofile', 'work_teaching_experience',
                      self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_managing_experience'
        db.add_column('auth_userprofile', 'work_managing_experience',
                      self.gf('django.db.models.fields.IntegerField')(null=True, db_index=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_qualification_category'
        db.add_column('auth_userprofile', 'work_qualification_category',
                      self.gf('django.db.models.fields.CharField')(max_length=10, null=True),
                      keep_default=False)

        # Adding field 'UserProfile.work_qualification_category_year'
        db.add_column('auth_userprofile', 'work_qualification_category_year',
                      self.gf('django.db.models.fields.IntegerField')(null=True, db_index=True),
                      keep_default=False)

        # Adding field 'UserProfile.contact_phone'
        db.add_column('auth_userprofile', 'contact_phone',
                      self.gf('django.db.models.fields.CharField')(max_length=10, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'UserProfile.qualification'
        db.add_column('auth_userprofile', 'qualification',
                      self.gf('django.db.models.fields.CharField')(max_length=30, null=True),
                      keep_default=False)

        # Deleting field 'UserProfile.lastname'
        db.delete_column('auth_userprofile', 'lastname')

        # Deleting field 'UserProfile.firstname'
        db.delete_column('auth_userprofile', 'firstname')

        # Deleting field 'UserProfile.middlename'
        db.delete_column('auth_userprofile', 'middlename')

        # Deleting field 'UserProfile.education_place'
        db.delete_column('auth_userprofile', 'education_place')

        # Deleting field 'UserProfile.education_year'
        db.delete_column('auth_userprofile', 'education_year')

        # Deleting field 'UserProfile.education_qualification'
        db.delete_column('auth_userprofile', 'education_qualification')

        # Deleting field 'UserProfile.education_specialty'
        db.delete_column('auth_userprofile', 'education_specialty')

        # Deleting field 'UserProfile.work_type'
        db.delete_column('auth_userprofile', 'work_type')

        # Deleting field 'UserProfile.work_number'
        db.delete_column('auth_userprofile', 'work_number')

        # Deleting field 'UserProfile.work_name'
        db.delete_column('auth_userprofile', 'work_name')

        # Deleting field 'UserProfile.work_login'
        db.delete_column('auth_userprofile', 'work_login')

        # Deleting field 'UserProfile.work_location'
        db.delete_column('auth_userprofile', 'work_location')

        # Deleting field 'UserProfile.work_occupation'
        db.delete_column('auth_userprofile', 'work_occupation')

        # Deleting field 'UserProfile.work_occupation_other'
        db.delete_column('auth_userprofile', 'work_occupation_other')

        # Deleting field 'UserProfile.work_teaching_experience'
        db.delete_column('auth_userprofile', 'work_teaching_experience')

        # Deleting field 'UserProfile.work_managing_experience'
        db.delete_column('auth_userprofile', 'work_managing_experience')

        # Deleting field 'UserProfile.work_qualification_category'
        db.delete_column('auth_userprofile', 'work_qualification_category')

        # Deleting field 'UserProfile.work_qualification_category_year'
        db.delete_column('auth_userprofile', 'work_qualification_category_year')

        # Deleting field 'UserProfile.contact_phone'
        db.delete_column('auth_userprofile', 'contact_phone')


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
        'student.courseenrollment': {
            'Meta': {'ordering': "('user', 'course_id')", 'unique_together': "(('user', 'course_id'),)", 'object_name': 'CourseEnrollment'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'default': "'honor'", 'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'student.courseenrollmentallowed': {
            'Meta': {'unique_together': "(('email', 'course_id'),)", 'object_name': 'CourseEnrollmentAllowed'},
            'auto_enroll': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'student.pendingemailchange': {
            'Meta': {'object_name': 'PendingEmailChange'},
            'activation_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_email': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'student.pendingnamechange': {
            'Meta': {'object_name': 'PendingNameChange'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'rationale': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'student.registration': {
            'Meta': {'object_name': 'Registration', 'db_table': "'auth_registration'"},
            'activation_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'student.testcenterregistration': {
            'Meta': {'object_name': 'TestCenterRegistration'},
            'accommodation_code': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'accommodation_request': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'authorization_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'client_authorization_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'confirmed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'eligibility_appointment_date_first': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'eligibility_appointment_date_last': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'exam_series_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'testcenter_user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['student.TestCenterUser']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'upload_error_message': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'upload_status': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20', 'blank': 'True'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'user_updated_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'student.testcenteruser': {
            'Meta': {'object_name': 'TestCenterUser'},
            'address_1': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'address_2': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'address_3': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'candidate_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'client_candidate_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'company_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'confirmed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '3', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'extension': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '8', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'fax_country_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'phone_country_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'db_index': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '16', 'blank': 'True'}),
            'processed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'salutation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'upload_error_message': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'upload_status': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20', 'blank': 'True'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['auth.User']", 'unique': 'True'}),
            'user_updated_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'student.userprofile': {
            'Meta': {'object_name': 'UserProfile', 'db_table': "'auth_userprofile'"},
            'allow_certificate': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'contact_phone': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'courseware': ('django.db.models.fields.CharField', [], {'default': "'course.xml'", 'max_length': '255', 'blank': 'True'}),
            'education_place': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'education_qualification': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'education_specialty': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'education_year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'firstname': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'db_index': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'goals': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'lastname': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'db_index': 'True'}),
            'level_of_education': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'mailing_address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'meta': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'middlename': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'work_location': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True'}),
            'work_login': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'work_managing_experience': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'work_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'work_number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'work_occupation': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'work_occupation_other': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'work_qualification_category': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'work_qualification_category_year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'work_teaching_experience': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'work_type': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True'}),
            'year_of_birth': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'student.usertestgroup': {
            'Meta': {'object_name': 'UserTestGroup'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'db_index': 'True', 'symmetrical': 'False'})
        }
    }

    complete_apps = ['student']