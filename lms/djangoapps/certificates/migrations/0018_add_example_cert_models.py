# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CertificateGenerationCourseSetting'
        db.create_table('certificates_certificategenerationcoursesetting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('course_key', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('certificates', ['CertificateGenerationCourseSetting'])

        # Adding model 'ExampleCertificate'
        db.create_table('certificates_examplecertificate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('example_cert_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['certificates.ExampleCertificateSet'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('uuid', self.gf('django.db.models.fields.CharField')(default='2017ea093523484cb355fac9c3e7a22b', unique=True, max_length=255, db_index=True)),
            ('access_key', self.gf('django.db.models.fields.CharField')(default='8dc842be46484291a65b9ea34c3a8af8', max_length=255, db_index=True)),
            ('full_name', self.gf('django.db.models.fields.CharField')(default=u'John Do\xeb', max_length=255)),
            ('template', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(default='started', max_length=255)),
            ('error_reason', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('download_url', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True)),
        ))
        db.create_index('certificates_examplecertificate', ['uuid', 'access_key'])
        db.send_create_signal('certificates', ['ExampleCertificate'])

        # Adding model 'ExampleCertificateSet'
        db.create_table('certificates_examplecertificateset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('course_key', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('certificates', ['ExampleCertificateSet'])

    def backwards(self, orm):
        # Deleting model 'CertificateGenerationCourseSetting'
        db.delete_table('certificates_certificategenerationcoursesetting')

        # Deleting model 'ExampleCertificate'
        db.delete_table('certificates_examplecertificate')

        # Deleting model 'ExampleCertificateSet'
        db.delete_table('certificates_examplecertificateset')

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
        'certificates.certificategenerationconfiguration': {
            'Meta': {'object_name': 'CertificateGenerationConfiguration'},
            'change_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'certificates.certificategenerationcoursesetting': {
            'Meta': {'object_name': 'CertificateGenerationCourseSetting'},
            'course_key': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        'certificates.certificatewhitelist': {
            'Meta': {'object_name': 'CertificateWhitelist'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'default': 'None', 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'whitelist': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'certificates.examplecertificate': {
            'Meta': {'object_name': 'ExampleCertificate'},
            'access_key': ('django.db.models.fields.CharField', [], {'default': "'616e8368b9b2458b8ef8217713275322'", 'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'download_url': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'error_reason': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'example_cert_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['certificates.ExampleCertificateSet']"}),
            'full_name': ('django.db.models.fields.CharField', [], {'default': "u'John Do\\xeb'", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'started'", 'max_length': '255'}),
            'template': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'f38e7389280d4776907ebf96ac728bac'", 'unique': 'True', 'max_length': '255', 'db_index': 'True'})
        },
        'certificates.examplecertificateset': {
            'Meta': {'object_name': 'ExampleCertificateSet'},
            'course_key': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        'certificates.generatedcertificate': {
            'Meta': {'unique_together': "(('user', 'course_id'),)", 'object_name': 'GeneratedCertificate'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'default': 'None', 'max_length': '255', 'blank': 'True'}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'distinction': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'download_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'download_uuid': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'error_reason': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512', 'blank': 'True'}),
            'grade': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '5', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'default': "'honor'", 'max_length': '32'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'unavailable'", 'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'verify_uuid': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['certificates']
