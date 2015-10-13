# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseUserGroupMembership'
        db.create_table('course_groups_courseusergroupmembership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_user_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['course_groups.CourseUserGroup'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('version', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('course_groups', ['CourseUserGroupMembership'])

        # Adding unique constraint on 'CourseUserGroupMembership', fields ['user', 'course_user_group']
        db.create_unique('course_groups_courseusergroupmembership', ['user_id', 'course_user_group_id'])

        # Removing M2M table for field users on 'CourseUserGroup'
        db.delete_table(db.shorten_name('course_groups_courseusergroup_users'))


    def backwards(self, orm):
        # Removing unique constraint on 'CourseUserGroupMembership', fields ['user', 'course_user_group']
        db.delete_unique('course_groups_courseusergroupmembership', ['user_id', 'course_user_group_id'])

        # Deleting model 'CourseUserGroupMembership'
        db.delete_table('course_groups_courseusergroupmembership')

        # Adding M2M table for field users on 'CourseUserGroup'
        m2m_table_name = db.shorten_name('course_groups_courseusergroup_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('courseusergroup', models.ForeignKey(orm['course_groups.courseusergroup'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['courseusergroup_id', 'user_id'])


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
        'course_groups.coursecohort': {
            'Meta': {'object_name': 'CourseCohort'},
            'assignment_type': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '20'}),
            'course_user_group': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'cohort'", 'unique': 'True', 'to': "orm['course_groups.CourseUserGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'course_groups.coursecohortssettings': {
            'Meta': {'object_name': 'CourseCohortsSettings'},
            '_cohorted_discussions': ('django.db.models.fields.TextField', [], {'null': 'True', 'db_column': "'cohorted_discussions'", 'blank': 'True'}),
            'always_cohort_inline_discussions': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_cohorted': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'course_groups.courseusergroup': {
            'Meta': {'unique_together': "(('name', 'course_id'),)", 'object_name': 'CourseUserGroup'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'group_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'related_name': "'course_groups'", 'symmetrical': 'False', 'through': "orm['course_groups.CourseUserGroupMembership']", 'to': "orm['auth.User']"})
        },
        'course_groups.courseusergroupmembership': {
            'Meta': {'unique_together': "(('user', 'course_user_group'),)", 'object_name': 'CourseUserGroupMembership'},
            'course_user_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['course_groups.CourseUserGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'version': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'course_groups.courseusergrouppartitiongroup': {
            'Meta': {'object_name': 'CourseUserGroupPartitionGroup'},
            'course_user_group': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['course_groups.CourseUserGroup']", 'unique': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group_id': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'partition_id': ('django.db.models.fields.IntegerField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['course_groups']