# -*- coding: utf-8 -*-
import datetime
import json
import logging

from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models, transaction, IntegrityError

from api_manager.models import GroupProfile
from openedx.core.djangoapps.user_api.models import UserPreference

log = logging.getLogger(__name__)


class Migration(SchemaMigration):

    def print_message(self, msg):
        print msg
        log.info(msg)

    def migrate_course_id(self, old_course_id):
        new_course_id = old_course_id
        if "slashes:" in old_course_id or "course-v1:" in old_course_id:
            new_course_id = old_course_id.replace("slashes:", "")
            new_course_id = new_course_id.replace("course-v1:", "")
            new_course_id = new_course_id.replace("+", "/")
        return new_course_id

    def migrate_content_id(self, old_content_id):
        new_content_id = old_content_id
        if "slashes:" in old_content_id or "course-v1:" in old_content_id:
            new_content_id = self._migrate_course_id(old_content_id)
        else:
            if "location:" in old_content_id:
                content_id = old_content_id.replace("location:", "")
                content_components = content_id.split('+')
                new_content_id = "i4x:/"
                for x in range(0, len(content_components)):
                    if x != 2:
                        new_content_id = "{}/{}".format(new_content_id, content_components[x])
        return new_content_id

    def dictfetchall(self, cursor):
        "Returns all rows from a cursor as a dict"
        desc = cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
        ]

    def forwards(self, orm):
        if not db.dry_run:
            try:
                user_preferences  = UserPreference.objects.filter(key='current_course_id')
                record_count = 0
                for pref in user_preferences:
                    if 'slashes:' in pref.value:
                        pref.value = self.migrate_course_id(pref.value)
                        pref.save()
                        record_count += 1
                log_msg = 'UserPreference "current_course_id" data cleanup complete! ({} records updated)'.format(record_count)
                self.print_message(log_msg)

                cursor = connection.cursor()
                cursor.execute("SELECT * FROM mentoring_answer LIMIT 0, 10000;")
                mentoring_answers = self.dictfetchall(cursor)
                record_count = 0
                for answer in mentoring_answers:
                    if 'slashes:' in answer['course_id']:
                        try:
                            command_string = "UPDATE mentoring_answer SET course_id = '{}' WHERE id = {};".format(self.migrate_course_id(answer['course_id']), answer['id'])
                            cursor.execute(command_string)
                        except IntegrityError:
                            command_string = "DELETE FROM mentoring_answer WHERE id = {}".format(answer['id'])
                            cursor.execute(command_string)
                        record_count += 1
                log_msg = 'MentoringAnswer "course_id" data cleanup complete! ({} records updated)'.format(record_count)
                self.print_message(log_msg)

            except Exception as e:
                log_msg = e.message
                self.print_message(log_msg)

    def backwards(self, orm):
        pass

    models = {
        'api_manager.coursecontentgrouprelationship': {
            'Meta': {'unique_together': "(('course_id', 'content_id', 'group_profile'),)", 'object_name': 'CourseContentGroupRelationship'},
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'group_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['api_manager.GroupProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'api_manager.coursegrouprelationship': {
            'Meta': {'object_name': 'CourseGroupRelationship'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'api_manager.coursemodulecompletion': {
            'Meta': {'object_name': 'CourseModuleCompletion'},
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'stage': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'course_completions'", 'to': "orm['auth.User']"})
        },
        'api_manager.groupprofile': {
            'Meta': {'object_name': 'GroupProfile', 'db_table': "'auth_groupprofile'"},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'group': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True'}),
            'group_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'api_manager.grouprelationship': {
            'Meta': {'object_name': 'GroupRelationship'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'group': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent_group': ('django.db.models.fields.related.ForeignKey', [], {'default': '0', 'related_name': "'child_groups'", 'null': 'True', 'blank': 'True', 'to': "orm['api_manager.GroupRelationship']"}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'api_manager.linkedgrouprelationship': {
            'Meta': {'object_name': 'LinkedGroupRelationship'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'from_group_relationship': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_group_relationships'", 'to': "orm['api_manager.GroupRelationship']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'record_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'to_group_relationship': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_group_relationships'", 'to': "orm['api_manager.GroupRelationship']"})
        },
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
        }
    }

    complete_apps = ['api_manager']
