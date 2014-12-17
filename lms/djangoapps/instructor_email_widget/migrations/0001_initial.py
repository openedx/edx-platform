# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GroupedQuery'
        db.create_table('instructor_email_widget_groupedquery', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('instructor_email_widget', ['GroupedQuery'])

        # Adding model 'SavedQuery'
        db.create_table('instructor_email_widget_savedquery', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('module_state_key', self.gf('xmodule_django.models.LocationKeyField')(max_length=255, db_column='module_id', db_index=True)),
            ('inclusion', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('filter_on', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('entity_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('query_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('instructor_email_widget', ['SavedQuery'])

        # Adding model 'TemporaryQuery'
        db.create_table('instructor_email_widget_temporaryquery', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True)),
            ('module_state_key', self.gf('xmodule_django.models.LocationKeyField')(max_length=255, db_column='module_id', db_index=True)),
            ('inclusion', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('filter_on', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, db_index=True, blank=True)),
            ('entity_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('query_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('done', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
        ))
        db.send_create_signal('instructor_email_widget', ['TemporaryQuery'])

        # Adding model 'StudentsForQuery'
        db.create_table('instructor_email_widget_studentsforquery', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('query', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['instructor_email_widget.TemporaryQuery'])),
            ('student', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('inclusion', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('instructor_email_widget', ['StudentsForQuery'])

        # Adding model 'GroupedTempQueryForSubquery'
        db.create_table('instructor_email_widget_groupedtempqueryforsubquery', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('grouped', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['instructor_email_widget.GroupedQuery'])),
            ('query', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['instructor_email_widget.TemporaryQuery'])),
        ))
        db.send_create_signal('instructor_email_widget', ['GroupedTempQueryForSubquery'])

        # Adding model 'SubqueryForGroupedQuery'
        db.create_table('instructor_email_widget_subqueryforgroupedquery', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('grouped', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['instructor_email_widget.GroupedQuery'])),
            ('query', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['instructor_email_widget.SavedQuery'])),
        ))
        db.send_create_signal('instructor_email_widget', ['SubqueryForGroupedQuery'])

    def backwards(self, orm):
        # Deleting model 'GroupedQuery'
        db.delete_table('instructor_email_widget_groupedquery')

        # Deleting model 'SavedQuery'
        db.delete_table('instructor_email_widget_savedquery')

        # Deleting model 'TemporaryQuery'
        db.delete_table('instructor_email_widget_temporaryquery')

        # Deleting model 'StudentsForQuery'
        db.delete_table('instructor_email_widget_studentsforquery')

        # Deleting model 'GroupedTempQueryForSubquery'
        db.delete_table('instructor_email_widget_groupedtempqueryforsubquery')

        # Deleting model 'SubqueryForGroupedQuery'
        db.delete_table('instructor_email_widget_subqueryforgroupedquery')

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
        'instructor_email_widget.groupedquery': {
            'Meta': {'object_name': 'GroupedQuery'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'instructor_email_widget.groupedtempqueryforsubquery': {
            'Meta': {'object_name': 'GroupedTempQueryForSubquery'},
            'grouped': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instructor_email_widget.GroupedQuery']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'query': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instructor_email_widget.TemporaryQuery']"})
        },
        'instructor_email_widget.savedquery': {
            'Meta': {'object_name': 'SavedQuery'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'entity_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'filter_on': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inclusion': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'module_state_key': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_column': "'module_id'", 'db_index': 'True'}),
            'query_type': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'instructor_email_widget.studentsforquery': {
            'Meta': {'object_name': 'StudentsForQuery'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inclusion': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'query': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instructor_email_widget.TemporaryQuery']"}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'instructor_email_widget.subqueryforgroupedquery': {
            'Meta': {'object_name': 'SubqueryForGroupedQuery'},
            'grouped': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instructor_email_widget.GroupedQuery']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'query': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instructor_email_widget.SavedQuery']"})
        },
        'instructor_email_widget.temporaryquery': {
            'Meta': {'object_name': 'TemporaryQuery'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'done': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'entity_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'filter_on': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inclusion': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'module_state_key': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_column': "'module_id'", 'db_index': 'True'}),
            'query_type': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['instructor_email_widget']
