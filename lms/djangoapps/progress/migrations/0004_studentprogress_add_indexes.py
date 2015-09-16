# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, missing-docstring
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    # pylint: disable=unused-argument
    def forwards(self, orm):
        # Adding index on 'StudentProgress', fields ['completions']
        db.create_index('progress_studentprogress', ['completions'])

        # Adding index on 'StudentProgress', fields ['modified']
        db.create_index('progress_studentprogress', ['modified'])

    # pylint: disable=unused-argument
    def backwards(self, orm):
        # Removing index on 'StudentProgress', fields ['modified']
        db.delete_index('progress_studentprogress', ['modified'])

        # Removing index on 'StudentProgress', fields ['completions']
        db.delete_index('progress_studentprogress', ['completions'])

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': (
                'django.db.models.fields.related.ManyToManyField', [], {
                    'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'
                }
            )
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')",
                     'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': (
                'django.db.models.fields.related.ForeignKey', [], {
                    'to': "orm['contenttypes.ContentType']"
                }
            ),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': (
                'django.db.models.fields.related.ManyToManyField', [], {
                    'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'
                }
            ),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': (
                'django.db.models.fields.related.ManyToManyField', [], {
                    'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'
                }
            ),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)",
                     'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'progress.coursemodulecompletion': {
            'Meta': {'object_name': 'CourseModuleCompletion'},
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'stage': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': (
                'django.db.models.fields.related.ForeignKey', [], {
                    'related_name': "'course_completions'", 'to': "orm['auth.User']"
                }
            )
        },
        'progress.studentprogress': {
            'Meta': {'unique_together': "(('user', 'course_id'),)", 'object_name': 'StudentProgress'},
            'completions': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'course_id': (
                'xmodule_django.models.CourseKeyField', [], {
                    'db_index': 'True', 'max_length': '255', 'blank': 'True'}
            ),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': (
                'model_utils.fields.AutoLastModifiedField', [], {
                    'default': 'datetime.datetime.now', 'db_index': 'True'
                }
            ),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'progress.studentprogresshistory': {
            'Meta': {'object_name': 'StudentProgressHistory'},
            'completions': ('django.db.models.fields.IntegerField', [], {}),
            'course_id': (
                'xmodule_django.models.CourseKeyField', [], {
                    'db_index': 'True', 'max_length': '255', 'blank': 'True'
                }
            ),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['progress']
