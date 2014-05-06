# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import DataMigration
from django.db import models
from xmodule.modulestore.django import loc_mapper
import re
from xmodule.modulestore.locations import SlashSeparatedCourseKey
from opaque_keys import InvalidKeyError
import bson.son
import logging
from django.db.models.query_utils import Q

log = logging.getLogger(__name__)


class Migration(DataMigration):
    """
    Converts course_creator, instructor_, staff_, and betatestuser_ to new table
    """

    GROUP_ENTRY_RE = re.compile(r'(?P<role_id>staff|instructor|beta_testers|course_creator_group)_?(?P<course_id_string>.*)')

    def forwards(self, orm):
        """
        Converts group table entries for write access and beta_test roles to course access roles table.
        """
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
        loc_map_collection = loc_mapper().location_map
        # b/c the Groups table had several entries for each course, we need to ensure we process each unique
        # course only once. The below datastructures help ensure that.
        hold = {}
        done = set()
        orgs = {}
        query = Q(name__startswith='course_creator_group')
        for role in ['staff', 'instructor', 'beta_testers', ]:
            query = query | Q(name__startswith=role)
        for group in orm['auth.Group'].objects.filter(query).all():
            def _migrate_users(correct_course_key, lower_org):
                """
                Get all the users from the old group and migrate to this course key in the new table
                """
                for user in orm['auth.user'].objects.filter(groups=group).all():
                    entry = orm['student.courseaccessrole'](
                        role=parsed_entry.group('role_id'), user=user,
                        org=correct_course_key.org, course_id=correct_course_key.to_deprecated_string()
                    )
                    entry.save()
                orgs[lower_org] = correct_course_key.org
                done.add(correct_course_key)

            # should this actually loop through all groups and log any which are not compliant? That is,
            # remove the above filter
            parsed_entry = self.GROUP_ENTRY_RE.match(group.name)
            if parsed_entry.group('role_id') == 'course_creator_group':
                for user in orm['auth.user'].objects.filter(groups=group).all():
                    entry = orm['student.courseaccessrole'](role=parsed_entry.group('role_id'), user=user)
                    entry.save()
            else:
                course_id_string = parsed_entry.group('course_id_string')
                try:
                    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id_string)
                    if course_key not in done:
                        # is the downcased version, get the normal cased one. loc_mapper() has no
                        # methods taking downcased SSCK; so, need to do it manually here
                        correct_course_key = self._map_downcased_ssck(course_key, loc_map_collection, done)
                        _migrate_users(correct_course_key, course_key.org)
                        done.add(course_key)
                except InvalidKeyError:
                    entry = loc_map_collection.find_one({
                        'course_id': re.compile(r'^{}$'.format(course_id_string), re.IGNORECASE)
                    })
                    if entry is None:
                        # not a course_id as far as we can tell
                        if course_id_string not in done:
                            hold[course_id_string] = group
                    else:
                        correct_course_key = self._cache_done_return_ssck(entry, done)
                        _migrate_users(correct_course_key, entry['lower_id']['org'])

        # see if any in hold ere missed above
        for not_ssck, group in hold.iteritems():
            if not_ssck not in done:
                if not_ssck in orgs:
                    # they have org permission
                    for user in orm['auth.user'].objects.filter(groups=group).all():
                        entry = orm['student.courseaccessrole'](
                            role=parsed_entry.group('role_id'), user=user,
                            org=orgs[not_ssck],
                        )
                        entry.save()
                else:
                    # should this just log or really make an effort to do the conversion?
                    log.warn("Didn't convert role %s", group.name)

    def backwards(self, orm):
        "Write your backwards methods here."
        # Since this migration is non-destructive (monotonically adds information), I'm not sure what
        # the semantic of backwards should be other than perhaps clearing the table.
        orm['student.courseaccessrole'].objects.all().delete()

    def _map_downcased_ssck(self, downcased_ssck, loc_map_collection, done):
        """
        Get the normal cased version of this downcased slash sep course key and add
        the lowercased locator form to done map
        """
        # given the regex, the son may be an overkill
        course_son = bson.son.SON([
            ('_id.org', re.compile(r'^{}$'.format(downcased_ssck.org), re.IGNORECASE)),
            ('_id.course', re.compile(r'^{}$'.format(downcased_ssck.course), re.IGNORECASE)),
            ('_id.name', re.compile(r'^{}$'.format(downcased_ssck.run), re.IGNORECASE)),
        ])
        entry = loc_map_collection.find_one(course_son)
        if entry:
            return self._cache_done_return_ssck(entry, done)
        else:
            return None

    def _cache_done_return_ssck(self, entry, done):
        """
        Add all the various formats which auth may use to the done set and return the ssck for the entry
        """
        # cache that the dotted form is done too
        if 'lower_course_id' in entry:
            done.add(entry['lower_course_id'])
        elif 'course_id' in entry:
            done.add(entry['course_id'].lower())
        elif 'lower_org' in entry:
            done.add('{}.{}'.format(entry['lower_org'], entry['lower_offering']))
        else:
            done.add('{}.{}'.format(entry['org'].lower(), entry['offering'].lower()))
        return SlashSeparatedCourseKey(*entry['_id'].values())


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
        'student.anonymoususerid': {
            'Meta': {'object_name': 'AnonymousUserId'},
            'anonymous_user_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'student.courseaccessrole': {
            'Meta': {'unique_together': "(('user', 'org', 'course_id', 'role'),)", 'object_name': 'CourseAccessRole'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'org': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'student.courseenrollment': {
            'Meta': {'ordering': "('user', 'course_id')", 'unique_together': "(('user', 'course_id'),)", 'object_name': 'CourseEnrollment'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'default': "'honor'", 'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'student.courseenrollmentallowed': {
            'Meta': {'unique_together': "(('email', 'course_id'),)", 'object_name': 'CourseEnrollmentAllowed'},
            'auto_enroll': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'student.loginfailures': {
            'Meta': {'object_name': 'LoginFailures'},
            'failure_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lockout_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'student.passwordhistory': {
            'Meta': {'object_name': 'PasswordHistory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'time_set': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'student.pendingemailchange': {
            'Meta': {'object_name': 'PendingEmailChange'},
            'activation_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_email': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'student.pendingnamechange': {
            'Meta': {'object_name': 'PendingNameChange'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'rationale': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'student.registration': {
            'Meta': {'object_name': 'Registration', 'db_table': "'auth_registration'"},
            'activation_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'student.userprofile': {
            'Meta': {'object_name': 'UserProfile', 'db_table': "'auth_userprofile'"},
            'allow_certificate': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'city': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'courseware': ('django.db.models.fields.CharField', [], {'default': "'course.xml'", 'max_length': '255', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'goals': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'level_of_education': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'mailing_address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'meta': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'year_of_birth': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'student.userstanding': {
            'Meta': {'object_name': 'UserStanding'},
            'account_status': ('django.db.models.fields.CharField', [], {'max_length': '31', 'blank': 'True'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'standing_last_changed_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'standing'", 'unique': 'True', 'to': "orm['auth.User']"})
        },
        'student.usertestgroup': {
            'Meta': {'object_name': 'UserTestGroup'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'db_index': 'True', 'symmetrical': 'False'})
        }
    }


    complete_apps = ['student']
    symmetrical = True
