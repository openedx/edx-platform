"""
WE'RE USING MIGRATIONS!

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

from xmodule.modulestore.django import modulestore

#from cache_toolbox import cache_model, cache_relation

log = logging.getLogger(__name__)

class UserProfile(models.Model):
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





################################# SIGNALS ######################################

def is_valid_course_id(course_id):
    """We check to both make sure that it's a valid course_id (and not 
    'default', or some other non-course DB name) and that we have a mapping
    for what database it belongs to."""
    course_ids = set(course.id for course in modulestore().get_courses())
    return (course_id in course_ids) and (course_id in settings.DATABASES)

def is_portal():
    """Are we in the portal pool? (in which case we'll have to replicate user
    updates). Right now, that means we have more than one database defined."""
    return len(settings.DATABASES) > 1

def replicate_enrollment(instance_method, **kwargs):
    log.debug("########## Enrollment replication called ############")
    instance = kwargs['instance']

    if not is_portal():
        log.debug("replicate_enrollment triggered, but we're not a portal so " +
                  "we're not propogating")
        return

    if not is_valid_course_id(instance.course_id):
        log.error("Don't know where to replicate to for course_id: {0}"
                  .format(instance.course_id))
        return

    # We create a _replicated attribute to differentiate the first save of this
    # model vs. the duplicate save we force on to the course database.
    if hasattr(instance, '_replicated'):
        log.debug("We've already replicated this -- stopping so we don't go " +
                  "into an infinite loop.")
        return 
    instance._replicated = True

    # instance_method is either CourseEnrollment.save or CourseEnrollment.delete
    # using is the entry in DATABASES we push to (we use course_ids for names)
    instance_method(instance, using=instance.course_id)

@receiver(post_save, sender=CourseEnrollment)
def replicate_enrollment_save(sender, **kwargs):
    return replicate_enrollment(CourseEnrollment.save, **kwargs)

@receiver(post_delete, sender=CourseEnrollment)
def replicate_enrollment_delete(sender, **kwargs):
    return replicate_enrollment(CourseEnrollment.delete, **kwargs)




