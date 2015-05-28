# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseOverviewDescriptor'
        db.create_table('course_overviews_courseoverviewdescriptor', (
            ('id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, primary_key=True, db_index=True)),
            ('modulestore_type', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('_location_str', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ispublic', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('static_asset_path', self.gf('django.db.models.fields.TextField')(default='')),
            ('user_partitions', self.gf('openedx.core.djangoapps.content.course_overviews.models.UserPartitionListField')(default='[]', null=True)),
            ('visible_to_staff_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('group_access', self.gf('openedx.core.djangoapps.content.course_overviews.models.GroupAccessDictField')(default='{}', null=True)),
            ('enrollment_start', self.gf('django.db.models.fields.DateField')(null=True)),
            ('enrollment_end', self.gf('django.db.models.fields.DateField')(null=True)),
            ('start', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2029, 12, 31, 0, 0), null=True)),
            ('end', self.gf('django.db.models.fields.DateField')(null=True)),
            ('advertised_start', self.gf('django.db.models.fields.TextField')(null=True)),
            ('pre_requisite_courses', self.gf('openedx.core.djangoapps.content.course_overviews.models.CourseIdListField')(null=True)),
            ('end_of_course_survey_url', self.gf('django.db.models.fields.TextField')(null=True)),
            ('display_name', self.gf('django.db.models.fields.TextField')(default='Empty', null=True)),
            ('mobile_available', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('facebook_url', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
            ('enrollment_domain', self.gf('django.db.models.fields.TextField')(null=True)),
            ('certificates_show_before_end', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('certificates_display_behavior', self.gf('django.db.models.fields.TextField')(default='end', null=True)),
            ('course_image', self.gf('django.db.models.fields.TextField')(default='images_course_image.jpg', null=True)),
            ('cert_name_short', self.gf('django.db.models.fields.TextField')(default='', null=True)),
            ('cert_name_long', self.gf('django.db.models.fields.TextField')(default='', null=True)),
            ('display_organization', self.gf('django.db.models.fields.TextField')(null=True)),
            ('display_coursenumber', self.gf('django.db.models.fields.TextField')(null=True)),
            ('invitation_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('catalog_visibility', self.gf('django.db.models.fields.TextField')(default='both', null=True)),
            ('social_sharing_url', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
        ))
        db.send_create_signal('course_overviews', ['CourseOverviewDescriptor'])


    def backwards(self, orm):
        # Deleting model 'CourseOverviewDescriptor'
        db.delete_table('course_overviews_courseoverviewdescriptor')


    models = {
        'course_overviews.courseoverviewdescriptor': {
            'Meta': {'object_name': 'CourseOverviewDescriptor'},
            '_location_str': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'advertised_start': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'catalog_visibility': ('django.db.models.fields.TextField', [], {'default': "'both'", 'null': 'True'}),
            'cert_name_long': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True'}),
            'cert_name_short': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True'}),
            'certificates_display_behavior': ('django.db.models.fields.TextField', [], {'default': "'end'", 'null': 'True'}),
            'certificates_show_before_end': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'course_image': ('django.db.models.fields.TextField', [], {'default': "'images_course_image.jpg'", 'null': 'True'}),
            'display_coursenumber': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'display_name': ('django.db.models.fields.TextField', [], {'default': "'Empty'", 'null': 'True'}),
            'display_organization': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_of_course_survey_url': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'enrollment_domain': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'enrollment_end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'enrollment_start': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'facebook_url': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'group_access': ('openedx.core.djangoapps.content.course_overviews.models.GroupAccessDictField', [], {'default': "'{}'", 'null': 'True'}),
            'id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'primary_key': 'True', 'db_index': 'True'}),
            'invitation_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ispublic': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'mobile_available': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modulestore_type': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'pre_requisite_courses': ('openedx.core.djangoapps.content.course_overviews.models.CourseIdListField', [], {'null': 'True'}),
            'social_sharing_url': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2029, 12, 31, 0, 0)', 'null': 'True'}),
            'static_asset_path': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'user_partitions': ('openedx.core.djangoapps.content.course_overviews.models.UserPartitionListField', [], {'default': "'[]'", 'null': 'True'}),
            'visible_to_staff_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['course_overviews']