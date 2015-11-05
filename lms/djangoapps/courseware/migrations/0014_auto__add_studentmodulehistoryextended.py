# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import dbs
from south.v2 import SchemaMigration
from django.db import models

default_db = dbs['default']
csmh_db = dbs['student_module_history']

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Create a new 'StudentModuleHistory' with an extended key space
        csmh_db.create_table('courseware_studentmodulehistory', (
            ('id', self.gf('courseware.fields.UnsignedBigIntAutoField')(primary_key=True)),
            ('course_key', self.gf('xmodule_django.models.CourseKeyField')(max_length=255)),
            ('usage_key', self.gf('xmodule_django.models.UsageKeyField')(max_length=255)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('version', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('state', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('grade', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('max_grade', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))

        if not default_db.dry_run:
            try:
                initial_id = 1000000 + orm.StudentModuleHistoryArchive.objects.all().latest('id').id
            except orm.StudentModuleHistoryArchive.DoesNotExist:
                initial_id = 0

            if csmh_db.backend_name == 'mysql':
                csmh_db.execute('ALTER TABLE courseware_studentmodulehistory AUTO_INCREMENT=%s', [initial_id])
            elif csmh_db.backend_name == 'sqlite3':
                # This is a hack to force sqlite to add new rows after the earlier rows we
                # want to migrate.
                orm.StudentModuleHistory(
                    id=initial_id,
                    course_key=None,
                    usage_key=None,
                    username="",
                    version="",
                    created=datetime.datetime.now(),
                ).save()

        csmh_db.send_create_signal('courseware', ['StudentModuleHistory'])


    def backwards(self, orm):
        # Revert to the old StudentModuleHistory table, but leave the data that was recorded in the interim.
        # This data will have to be manually cleaned up before the migration can be moved forward again.

        csmh_db.rename_table('courseware_studentmodulehistory', 'courseware_studentmodulehistory_extended_archive')


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
        'courseware.offlinecomputedgrade': {
            'Meta': {'unique_together': "(('user', 'course_id'),)", 'object_name': 'OfflineComputedGrade'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'gradeset': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'courseware.offlinecomputedgradelog': {
            'Meta': {'ordering': "['-created']", 'object_name': 'OfflineComputedGradeLog'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nstudents': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'seconds': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'courseware.studentfieldoverride': {
            'Meta': {'unique_together': "(('course_id', 'field', 'location', 'student'),)", 'object_name': 'StudentFieldOverride'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        },
        'courseware.studentmodule': {
            'Meta': {'unique_together': "(('student', 'module_state_key', 'course_id'),)", 'object_name': 'StudentModule'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'done': ('django.db.models.fields.CharField', [], {'default': "'na'", 'max_length': '8', 'db_index': 'True'}),
            'grade': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'module_state_key': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_column': "'module_id'", 'db_index': 'True'}),
            'module_type': ('django.db.models.fields.CharField', [], {'default': "'problem'", 'max_length': '32', 'db_index': 'True'}),
            'state': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'courseware.studentmodulehistoryarchive': {
            'Meta': {'object_name': 'StudentModuleHistoryArchive', 'db_table': "'courseware_studentmodulehistory'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'student_module': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['courseware.StudentModule']"}),
            'version': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'courseware.studentmodulehistory': {
            'Meta': {'object_name': 'StudentModuleHistory'},
            'course_key': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('courseware.fields.UnsignedBigIntAutoField', [], {'primary_key': 'True'}),
            'max_grade': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'usage_key': ('xmodule_django.models.UsageKeyField', [], {'max_length': '255'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'version': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'courseware.xmodulestudentinfofield': {
            'Meta': {'unique_together': "(('student', 'field_name'),)", 'object_name': 'XModuleStudentInfoField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        },
        'courseware.xmodulestudentprefsfield': {
            'Meta': {'unique_together': "(('student', 'module_type', 'field_name'),)", 'object_name': 'XModuleStudentPrefsField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'module_type': ('xmodule_django.models.BlockTypeKeyField', [], {'max_length': '64', 'db_index': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        },
        'courseware.xmoduleuserstatesummaryfield': {
            'Meta': {'unique_together': "(('usage_id', 'field_name'),)", 'object_name': 'XModuleUserStateSummaryField'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'usage_id': ('xmodule_django.models.LocationKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'default': "'null'"})
        }
    }

    complete_apps = ['courseware']
