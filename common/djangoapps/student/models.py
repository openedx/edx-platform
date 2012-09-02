"""
Models for Student Information

Replication Notes

In our live deployment, we intend to run in a scenario where there is a pool of
Portal servers that hold the canoncial user information and that user 
information is replicated to slave Course server pools. Each Course has a set of
servers that serves only its content and has users that are relevant only to it.

We replicate the following tables into the Course DBs where the user is 
enrolled. Only the Portal servers should ever write to these models.
* UserProfile
* CourseEnrollment

We do a partial replication of:
* User -- Askbot extends this and uses the extra fields, so we replicate only
          the stuff that comes with basic django_auth and ignore the rest.)

There are a couple different scenarios:

1. There's an update of User or UserProfile -- replicate it to all Course DBs
   that the user is enrolled in (found via CourseEnrollment).
2. There's a change in CourseEnrollment. We need to push copies of UserProfile,
   CourseEnrollment, and the base fields in User

Migration Notes

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the mitx dir
2. django-admin.py schemamigration student --auto --settings=lms.envs.dev --pythonpath=. description_of_your_change
3. Add the migration file created in mitx/common/djangoapps/student/migrations/
"""
from datetime import datetime
import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_countries import CountryField

from django.db.models.signals import post_save
from django.dispatch import receiver

from functools import partial

import comment_client as cc
from django_comment_client.models import Role, Permission

import logging

from xmodule.modulestore.django import modulestore

#from cache_toolbox import cache_model, cache_relation

log = logging.getLogger(__name__)

class UserProfile(models.Model):
    """This is where we store all the user demographic fields. We have a 
    separate table for this rather than extending the built-in Django auth_user.

    Notes:
        * Some fields are legacy ones from the first run of 6.002, from which 
          we imported many users.
        * Fields like name and address are intentionally open ended, to account
          for international variations. An unfortunate side-effect is that we
          cannot efficiently sort on last names for instance.

    Replication:
        * Only the Portal servers should ever modify this information.
        * All fields are replicated into relevant Course databases

    Some of the fields are legacy ones that were captured during the initial
    MITx fall prototype.
    """

    class Meta:
        db_table = "auth_userprofile"

    ## CRITICAL TODO/SECURITY
    # Sanitize all fields.
    # This is not visible to other users, but could introduce holes later
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='profile')
    name = models.CharField(blank=True, max_length=255, db_index=True)

    meta = models.TextField(blank=True)  # JSON dictionary for future expansion
    courseware = models.CharField(blank=True, max_length=255, default='course.xml')

    # Location is no longer used, but is held here for backwards compatibility
    # for users imported from our first class.
    language = models.CharField(blank=True, max_length=255, db_index=True)
    location = models.CharField(blank=True, max_length=255, db_index=True)

    # Optional demographic data we started capturing from Fall 2012
    this_year = datetime.now().year
    VALID_YEARS = range(this_year, this_year - 120, -1)
    year_of_birth = models.IntegerField(blank=True, null=True, db_index=True)
    GENDER_CHOICES = (('m', 'Male'), ('f', 'Female'), ('o', 'Other'))
    gender = models.CharField(blank=True, null=True, max_length=6, db_index=True,
                              choices=GENDER_CHOICES)
    LEVEL_OF_EDUCATION_CHOICES = (('p_se', 'Doctorate in science or engineering'),
                                  ('p_oth', 'Doctorate in another field'),
                                  ('m', "Master's or professional degree"),
                                  ('b', "Bachelor's degree"),
                                  ('hs', "Secondary/high school"),
                                  ('jhs', "Junior secondary/junior high/middle school"),
                                  ('el', "Elementary/primary school"),
                                  ('none', "None"),
                                  ('other', "Other"))
    level_of_education = models.CharField(
                            blank=True, null=True, max_length=6, db_index=True,
                            choices=LEVEL_OF_EDUCATION_CHOICES
                         )
    mailing_address = models.TextField(blank=True, null=True)
    goals = models.TextField(blank=True, null=True)

    def get_meta(self):
        js_str = self.meta
        if not js_str:
            js_str = dict()
        else:
            js_str = json.loads(self.meta)

        return js_str

    def set_meta(self, js):
        self.meta = json.dumps(js)


## TODO: Should be renamed to generic UserGroup, and possibly
# Given an optional field for type of group
class UserTestGroup(models.Model):
    users = models.ManyToManyField(User, db_index=True)
    name = models.CharField(blank=False, max_length=32, db_index=True)
    description = models.TextField(blank=True)


class Registration(models.Model):
    ''' Allows us to wait for e-mail before user is registered. A
        registration profile is created when the user creates an
        account, but that account is inactive. Once the user clicks
        on the activation key, it becomes active. '''
    class Meta:
        db_table = "auth_registration"

    user = models.ForeignKey(User, unique=True)
    activation_key = models.CharField(('activation key'), max_length=32, unique=True, db_index=True)

    def register(self, user):
        # MINOR TODO: Switch to crypto-secure key
        self.activation_key = uuid.uuid4().hex
        self.user = user
        self.save()

    def activate(self):
        self.user.is_active = True
        self.user.save()
        #self.delete()


class PendingNameChange(models.Model):
    user = models.OneToOneField(User, unique=True, db_index=True)
    new_name = models.CharField(blank=True, max_length=255)
    rationale = models.CharField(blank=True, max_length=1024)


class PendingEmailChange(models.Model):
    user = models.OneToOneField(User, unique=True, db_index=True)
    new_email = models.CharField(blank=True, max_length=255, db_index=True)
    activation_key = models.CharField(('activation key'), max_length=32, unique=True, db_index=True)

class CourseEnrollment(models.Model):
    user = models.ForeignKey(User)
    course_id = models.CharField(max_length=255, db_index=True)

    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)

    class Meta:
        unique_together = (('user', 'course_id'), )

    def __unicode__(self):
        return "%s: %s (%s)" % (self.user,self.course_id,self.created)

@receiver(post_save, sender=CourseEnrollment)
def assign_default_role(sender, instance, **kwargs):
    if instance.user.is_staff:
        role = Role.objects.get_or_create(course_id=instance.course_id, name="Moderator")[0]
    else:
        role = Role.objects.get_or_create(course_id=instance.course_id, name="Student")[0]

    logging.info("assign_default_role: adding %s as %s" % (instance.user, role))
    instance.user.roles.add(role)

#cache_relation(User.profile)

#### Helper methods for use from python manage.py shell.


def get_user(email):
    u = User.objects.get(email=email)
    up = UserProfile.objects.get(user=u)
    return u, up


def user_info(email):
    u, up = get_user(email)
    print "User id", u.id
    print "Username", u.username
    print "E-mail", u.email
    print "Name", up.name
    print "Location", up.location
    print "Language", up.language
    return u, up


def change_email(old_email, new_email):
    u = User.objects.get(email=old_email)
    u.email = new_email
    u.save()


def change_name(email, new_name):
    u, up = get_user(email)
    up.name = new_name
    up.save()


def user_count():
    print "All users", User.objects.all().count()
    print "Active users", User.objects.filter(is_active=True).count()
    return User.objects.all().count()


def active_user_count():
    return User.objects.filter(is_active=True).count()


def create_group(name, description):
    utg = UserTestGroup()
    utg.name = name
    utg.description = description
    utg.save()


def add_user_to_group(user, group):
    utg = UserTestGroup.objects.get(name=group)
    utg.users.add(User.objects.get(username=user))
    utg.save()


def remove_user_from_group(user, group):
    utg = UserTestGroup.objects.get(name=group)
    utg.users.remove(User.objects.get(username=user))
    utg.save()

default_groups = {'email_future_courses': 'Receive e-mails about future MITx courses',
                  'email_helpers': 'Receive e-mails about how to help with MITx',
                  'mitx_unenroll': 'Fully unenrolled -- no further communications',
                  '6002x_unenroll': 'Took and dropped 6002x'}


def add_user_to_default_group(user, group):
    try:
        utg = UserTestGroup.objects.get(name=group)
    except UserTestGroup.DoesNotExist:
        utg = UserTestGroup()
        utg.name = group
        utg.description = default_groups[group]
        utg.save()
    utg.users.add(User.objects.get(username=user))
    utg.save()

@receiver(post_save, sender=User)
def update_user_information(sender, instance, created, **kwargs):
    try:
        cc_user = cc.User.from_django_user(instance)
        cc_user.save()
    except Exception as e:
        log = logging.getLogger("mitx.discussion")
        log.error(unicode(e))
        log.error("update user info to discussion failed for user with id: " + str(instance.id))

########################## REPLICATION SIGNALS #################################
# @receiver(post_save, sender=User)
def replicate_user_save(sender, **kwargs):
    user_obj = kwargs['instance']
    if not should_replicate(user_obj):
        return
    for course_db_name in db_names_to_replicate_to(user_obj.id):
        replicate_user(user_obj, course_db_name)

# @receiver(post_save, sender=CourseEnrollment)
def replicate_enrollment_save(sender, **kwargs):
    """This is called when a Student enrolls in a course. It has to do the 
    following:

    1. Make sure the User is copied into the Course DB. It may already exist 
       (someone deleting and re-adding a course). This has to happen first or
       the foreign key constraint breaks.
    2. Replicate the CourseEnrollment.
    3. Replicate the UserProfile.
    """
    if not is_portal():
        return

    enrollment_obj = kwargs['instance']
    log.debug("Replicating user because of new enrollment")
    for course_db_name in db_names_to_replicate_to(enrollment_obj.user.id):
        replicate_user(enrollment_obj.user, course_db_name)

    log.debug("Replicating enrollment because of new enrollment")
    replicate_model(CourseEnrollment.save, enrollment_obj, enrollment_obj.user_id)

    log.debug("Replicating user profile because of new enrollment")
    user_profile = UserProfile.objects.get(user_id=enrollment_obj.user_id)
    replicate_model(UserProfile.save, user_profile, enrollment_obj.user_id)
 
# @receiver(post_delete, sender=CourseEnrollment)
def replicate_enrollment_delete(sender, **kwargs):
    enrollment_obj = kwargs['instance']
    return replicate_model(CourseEnrollment.delete, enrollment_obj, enrollment_obj.user_id)
 
# @receiver(post_save, sender=UserProfile)
def replicate_userprofile_save(sender, **kwargs):
    """We just updated the UserProfile (say an update to the name), so push that
    change to all Course DBs that we're enrolled in."""
    user_profile_obj = kwargs['instance']
    return replicate_model(UserProfile.save, user_profile_obj, user_profile_obj.user_id)

 
######### Replication functions #########
USER_FIELDS_TO_COPY = ["id", "username", "first_name", "last_name", "email",
                       "password", "is_staff", "is_active", "is_superuser",
                       "last_login", "date_joined"]

def replicate_user(portal_user, course_db_name):
    """Replicate a User to the correct Course DB. This is more complicated than
    it should be because Askbot extends the auth_user table and adds its own 
    fields. So we need to only push changes to the standard fields and leave
    the rest alone so that Askbot changes at the Course DB level don't get 
    overridden.
    """
    try:
        course_user = User.objects.using(course_db_name).get(id=portal_user.id)
        log.debug("User {0} found in Course DB, replicating fields to {1}"
                  .format(course_user, course_db_name))
    except User.DoesNotExist:
        log.debug("User {0} not found in Course DB, creating copy in {1}"
                  .format(portal_user, course_db_name))
        course_user = User()

    for field in USER_FIELDS_TO_COPY:
        setattr(course_user, field, getattr(portal_user, field))

    mark_handled(course_user)
    course_user.save(using=course_db_name)
    unmark(course_user)

def replicate_model(model_method, instance, user_id):
    """
    model_method is the model action that we want replicated. For instance, 
                 UserProfile.save
    """
    if not should_replicate(instance):
        return

    course_db_names = db_names_to_replicate_to(user_id)
    log.debug("Replicating {0} for user {1} to DBs: {2}"
              .format(model_method, user_id, course_db_names))

    mark_handled(instance)
    for db_name in course_db_names:
        model_method(instance, using=db_name)
    unmark(instance)

######### Replication Helpers #########

def is_valid_course_id(course_id):
    """Right now, the only database that's not a course database is 'default'.
    I had nicer checking in here originally -- it would scan the courses that
    were in the system and only let you choose that. But it was annoying to run
    tests with, since we don't have course data for some for our course test 
    databases. Hence the lazy version.
    """
    return course_id != 'default'

def is_portal():
    """Are we in the portal pool? Only Portal servers are allowed to replicate
    their changes. For now, only Portal servers see multiple DBs, so we use
    that to decide."""
    return len(settings.DATABASES) > 1

def db_names_to_replicate_to(user_id):
    """Return a list of DB names that this user_id is enrolled in."""
    return [c.course_id
            for c in CourseEnrollment.objects.filter(user_id=user_id)
            if is_valid_course_id(c.course_id)]

def marked_handled(instance):
    """Have we marked this instance as being handled to avoid infinite loops
    caused by saving models in post_save hooks for the same models?"""
    return hasattr(instance, '_do_not_copy_to_course_db') and instance._do_not_copy_to_course_db

def mark_handled(instance):
    """You have to mark your instance with this function or else we'll go into
    an infinite loop since we're putting listeners on Model saves/deletes and 
    the act of replication requires us to call the same model method.

    We create a _replicated attribute to differentiate the first save of this
    model vs. the duplicate save we force on to the course database. Kind of
    a hack -- suggestions welcome.
    """
    instance._do_not_copy_to_course_db = True

def unmark(instance):
    """If we don't unmark a model after we do replication, then consecutive 
    save() calls won't be properly replicated."""
    instance._do_not_copy_to_course_db = False

def should_replicate(instance):
    """Should this instance be replicated? We need to be a Portal server and
    the instance has to not have been marked_handled."""
    if marked_handled(instance):
        # Basically, avoid an infinite loop. You should 
        log.debug("{0} should not be replicated because it's been marked"
                  .format(instance))
        return False
    if not is_portal():
        log.debug("{0} should not be replicated because we're not a portal."
                  .format(instance))
        return False
    return True
