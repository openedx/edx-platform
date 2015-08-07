# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from opaque_keys import InvalidKeyError

class Migration(DataMigration):

    def forwards(self, orm):
        "Convert CCX Memberships to Course Enrollments."
        from ccx_keys.locator import CCXLocator
        memberships = orm['ccx.CcxMembership'].objects.select_related('ccx', 'student').all()
        for membership in memberships:
            ccx = membership.ccx
            try:
                course_key = CCXLocator.from_course_locator(ccx.course_id, ccx.id)
                enrollment, created = orm['student.CourseEnrollment'].objects.get_or_create(
                    user=membership.student,
                    course_id=course_key,
                )
            except InvalidKeyError:
                membership.delete()


    def backwards(self, orm):
        """In the future, here we will convert back CCX Course Enrollments to CCX
           Memberships.
        """

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
        'ccx.ccxfieldoverride': {
            'Meta': {'unique_together': "(('ccx', 'location', 'field'),)", 'object_name': 'CcxFieldOverride'},
            'ccx': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ccx.CustomCourseForEdX']"}),
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        },
        'ccx.customcourseforedx': {
            'Meta': {'object_name': 'CustomCourseForEdX'},
            'coach': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'ccx.ccxmembership': {
            'Meta': {'object_name': 'CcxMembership'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': False}),
            'ccx': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ccx.CustomCourseForEdX']"}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'student.courseenrollment': {
            'Meta': {'object_name': 'CourseEnrollment'},
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': True}),
            'mode': ('django.db.models.fields.CharField', [], {'max_length': '100', 'default': '"honor"'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['ccx', 'ccx']
    symmetrical = True
