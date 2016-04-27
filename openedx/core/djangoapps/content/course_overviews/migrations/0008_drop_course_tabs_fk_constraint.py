# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Foreign keys aren't enforced by default on our version of SQLite3, and
        # trying to delete them will throw an error. See:
        #   http://south.aeracode.org/ticket/775
        if db.backend_name != 'sqlite3':
            db.delete_foreign_key('course_overviews_courseoverviewtab', 'course_overview_id')

    def backwards(self, orm):
        pass

    models = {
        'course_overviews.courseoverview': {
            'Meta': {'object_name': 'CourseOverview'},
            '_location': ('xmodule_django.models.UsageKeyField', [], {'max_length': '255'}),
            '_pre_requisite_courses_json': ('django.db.models.fields.TextField', [], {}),
            'advertised_start': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'cert_html_view_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cert_name_long': ('django.db.models.fields.TextField', [], {}),
            'cert_name_short': ('django.db.models.fields.TextField', [], {}),
            'certificates_display_behavior': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'certificates_show_before_end': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'course_image_url': ('django.db.models.fields.TextField', [], {}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'days_early_for_beta': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'display_name': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'display_number_with_default': ('django.db.models.fields.TextField', [], {}),
            'display_org_with_default': ('django.db.models.fields.TextField', [], {}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'end_of_course_survey_url': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'enrollment_domain': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'enrollment_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'enrollment_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'facebook_url': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'has_any_active_web_certificate': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'primary_key': 'True', 'db_index': 'True'}),
            'invitation_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lowest_passing_grade': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'max_student_enrollments_allowed': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'mobile_available': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'social_sharing_url': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {}),
            'visible_to_staff_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'course_overviews.courseoverviewtab': {
            'Meta': {'object_name': 'CourseOverviewTab'},
            'course_overview': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tabs'", 'to': "orm['course_overviews.CourseOverview']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tab_id': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['course_overviews']