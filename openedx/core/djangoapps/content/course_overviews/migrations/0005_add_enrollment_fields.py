# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # The default values for these new columns may not match the actual
        # values of courses already present in the table. To ensure that the
        # cached values are correct, we must clear the table before adding any
        # new columns.
        db.clear_table('course_overviews_courseoverview')

        # Adding field 'CourseOverview.enrollment_start'
        db.add_column('course_overviews_courseoverview', 'enrollment_start',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'CourseOverview.enrollment_end'
        db.add_column('course_overviews_courseoverview', 'enrollment_end',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'CourseOverview.enrollment_domain'
        db.add_column('course_overviews_courseoverview', 'enrollment_domain',
                      self.gf('django.db.models.fields.TextField')(null=True),
                      keep_default=False)

        # Adding field 'CourseOverview.invitation_only'
        db.add_column('course_overviews_courseoverview', 'invitation_only',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'CourseOverview.max_student_enrollments_allowed'
        db.add_column('course_overviews_courseoverview', 'max_student_enrollments_allowed',
                      self.gf('django.db.models.fields.IntegerField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'CourseOverview.enrollment_start'
        db.delete_column('course_overviews_courseoverview', 'enrollment_start')

        # Deleting field 'CourseOverview.enrollment_end'
        db.delete_column('course_overviews_courseoverview', 'enrollment_end')

        # Deleting field 'CourseOverview.enrollment_domain'
        db.delete_column('course_overviews_courseoverview', 'enrollment_domain')

        # Deleting field 'CourseOverview.invitation_only'
        db.delete_column('course_overviews_courseoverview', 'invitation_only')

        # Deleting field 'CourseOverview.max_student_enrollments_allowed'
        db.delete_column('course_overviews_courseoverview', 'max_student_enrollments_allowed')


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
            'lowest_passing_grade': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2', 'null': 'True'}),
            'max_student_enrollments_allowed': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'mobile_available': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'social_sharing_url': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'visible_to_staff_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['course_overviews']