# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'VerificationCheckpoint'
        db.create_table('verify_student_verificationcheckpoint', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('checkpoint_name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('verify_student', ['VerificationCheckpoint'])

        # Adding M2M table for field photo_verification on 'VerificationCheckpoint'
        m2m_table_name = db.shorten_name('verify_student_verificationcheckpoint_photo_verification')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('verificationcheckpoint', models.ForeignKey(orm['verify_student.verificationcheckpoint'], null=False)),
            ('softwaresecurephotoverification', models.ForeignKey(orm['verify_student.softwaresecurephotoverification'], null=False))
        ))
        db.create_unique(m2m_table_name, ['verificationcheckpoint_id', 'softwaresecurephotoverification_id'])

        # Adding unique constraint on 'VerificationCheckpoint', fields ['course_id', 'checkpoint_name']
        db.create_unique('verify_student_verificationcheckpoint', ['course_id', 'checkpoint_name'])

        # Adding model 'VerificationStatus'
        db.create_table('verify_student_verificationstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('checkpoint', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['verify_student.VerificationCheckpoint'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('response', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('error', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('verify_student', ['VerificationStatus'])


    def backwards(self, orm):
        # Removing unique constraint on 'VerificationCheckpoint', fields ['course_id', 'checkpoint_name']
        db.delete_unique('verify_student_verificationcheckpoint', ['course_id', 'checkpoint_name'])

        # Deleting model 'VerificationCheckpoint'
        db.delete_table('verify_student_verificationcheckpoint')

        # Removing M2M table for field photo_verification on 'VerificationCheckpoint'
        db.delete_table(db.shorten_name('verify_student_verificationcheckpoint_photo_verification'))

        # Deleting model 'VerificationStatus'
        db.delete_table('verify_student_verificationstatus')


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
        'reverification.midcoursereverificationwindow': {
            'Meta': {'object_name': 'MidcourseReverificationWindow'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'verify_student.softwaresecurephotoverification': {
            'Meta': {'ordering': "['-created_at']", 'object_name': 'SoftwareSecurePhotoVerification'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'error_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'error_msg': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'face_image_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'photo_id_image_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'}),
            'photo_id_key': ('django.db.models.fields.TextField', [], {'max_length': '1024'}),
            'receipt_id': ('django.db.models.fields.CharField', [], {'default': "'4f091843-1377-4d3b-af5d-3a4ae3d17943'", 'max_length': '255', 'db_index': 'True'}),
            'reviewing_service': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'reviewing_user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'photo_verifications_reviewed'", 'null': 'True', 'to': "orm['auth.User']"}),
            'status': ('model_utils.fields.StatusField', [], {'default': "'created'", 'max_length': '100', u'no_check_for_status': 'True'}),
            'status_changed': ('model_utils.fields.MonitorField', [], {'default': 'datetime.datetime.now', u'monitor': "u'status'"}),
            'submitted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'window': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reverification.MidcourseReverificationWindow']", 'null': 'True'})
        },
        'verify_student.verificationcheckpoint': {
            'Meta': {'unique_together': "(('course_id', 'checkpoint_name'),)", 'object_name': 'VerificationCheckpoint'},
            'checkpoint_name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'photo_verification': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['verify_student.SoftwareSecurePhotoVerification']", 'symmetrical': 'False'})
        },
        'verify_student.verificationstatus': {
            'Meta': {'object_name': 'VerificationStatus'},
            'checkpoint': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['verify_student.VerificationCheckpoint']"}),
            'error': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['verify_student']
