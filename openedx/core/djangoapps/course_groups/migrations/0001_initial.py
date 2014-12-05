# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models, connection


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CourseUserGroup'

        def table_exists(name):
            return name in connection.introspection.table_names()

        def index_exists(table_name, column_name):
            return column_name in connection.introspection.get_indexes(connection.cursor(), table_name)

        # Since this djangoapp has been converted to south migrations after-the-fact,
        # these tables/indexes should already exist when migrating an existing installation.
        if not (
            table_exists('course_groups_courseusergroup') and
            index_exists('course_groups_courseusergroup', 'name') and
            index_exists('course_groups_courseusergroup', 'course_id') and
            table_exists('course_groups_courseusergroup_users') and
            index_exists('course_groups_courseusergroup_users', 'courseusergroup_id') and
            index_exists('course_groups_courseusergroup_users', 'user_id')
        ):
            db.create_table('course_groups_courseusergroup', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
                ('group_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ))
            db.send_create_signal('course_groups', ['CourseUserGroup'])

            # Adding unique constraint on 'CourseUserGroup', fields ['name', 'course_id']
            db.create_unique('course_groups_courseusergroup', ['name', 'course_id'])

            # Adding M2M table for field users on 'CourseUserGroup'
            db.create_table('course_groups_courseusergroup_users', (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('courseusergroup', models.ForeignKey(orm['course_groups.courseusergroup'], null=False)),
                ('user', models.ForeignKey(orm['auth.user'], null=False))
            ))
            db.create_unique('course_groups_courseusergroup_users', ['courseusergroup_id', 'user_id'])

    def backwards(self, orm):
        # Removing unique constraint on 'CourseUserGroup', fields ['name', 'course_id']
        db.delete_unique('course_groups_courseusergroup', ['name', 'course_id'])

        # Deleting model 'CourseUserGroup'
        db.delete_table('course_groups_courseusergroup')

        # Removing M2M table for field users on 'CourseUserGroup'
        db.delete_table('course_groups_courseusergroup_users')

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
        'course_groups.courseusergroup': {
            'Meta': {'unique_together': "(('name', 'course_id'),)", 'object_name': 'CourseUserGroup'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'group_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'related_name': "'course_groups'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['course_groups']
