# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models, IntegrityError, transaction


class Migration(DataMigration):

    def forwards(self, orm):
        # Matches CourseUserGroup.COHORT
        cohort_type = 'cohort'

        for cohort_group in orm.CourseUserGroup.objects.all():
            for user in cohort_group.users.all():
                current_course_groups = orm.CourseUserGroup.objects.filter(
                    course_id=cohort_group.course_id,
                    users__id=user.id,
                    group_type=cohort_type
                )
                current_user_groups = user.course_groups.filter(
                    course_id=cohort_group.course_id,
                    group_type=cohort_type
                )

                unioned_set = set(current_course_groups).union(set(current_user_groups))

                # Per product guidance, fix problem users by arbitrarily choosing a single membership to retain
                arbitrary_cohort_to_keep = unioned_set.pop()

                try:
                    membership = orm.CohortMembership(
                        course_user_group=arbitrary_cohort_to_keep,
                        user=user,
                        course_id=arbitrary_cohort_to_keep.course_id
                    )
                    membership.save()
                except IntegrityError:
                    # It's possible a user already has a conflicting entry in the db. Treat that as correct.
                    unioned_set.add(arbitrary_cohort_to_keep)
                    try:
                        valid_membership = orm.CohortMembership.objects.get(
                            course_id = cohort_group.course_id,
                            user__id=user.id
                        )
                        actual_cohort_to_keep = orm.CourseUserGroup.objects.get(
                            id=valid_membership.course_user_group.id
                        )
                        unioned_set.remove(actual_cohort_to_keep)
                    except KeyError:
                        actual_cohort_to_keep.users.add(user)

                for cohort_itr in unioned_set:
                    cohort_itr.users.remove(user)
                    user.course_groups.remove(cohort_itr)

    def backwards(self, orm):
        # A backwards migration just means dropping the table, which 0005 handles in its backwards() method
        pass

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
        'course_groups.cohortmembership': {
            'Meta': {'unique_together': "(('user', 'course_id'),)", 'object_name': 'CohortMembership'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255'}),
            'course_user_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['course_groups.CourseUserGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
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
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'related_name': "'course_groups'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
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
