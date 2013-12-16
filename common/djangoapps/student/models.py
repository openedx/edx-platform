"""
Models for User Information (students, staff, etc)

Migration Notes

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms schemamigration student --auto description_of_your_change
3. Add the migration file created in edx-platform/common/djangoapps/student/migrations/
"""
from datetime import datetime
import hashlib
import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from cities.models import City
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
import django.dispatch
from django.forms import ModelForm, forms
from django.core.exceptions import ObjectDoesNotExist

from course_modes.models import CourseMode
import lms.lib.comment_client as cc
from pytz import UTC
import crum

from track import contexts
from track.views import server_track
from eventtracking import tracker
from django.utils.translation import ugettext as _


unenroll_done = Signal(providing_args=["course_enrollment"])

log = logging.getLogger(__name__)
AUDIT_LOG = logging.getLogger("audit")


class AnonymousUserId(models.Model):
    """
    This table contains user, course_Id and anonymous_user_id

    Purpose of this table is to provide user by anonymous_user_id.

    We are generating anonymous_user_id using md5 algorithm, so resulting length will always be 16 bytes.
    http://docs.python.org/2/library/md5.html#md5.digest_size
    """
    user = models.ForeignKey(User, db_index=True)
    anonymous_user_id = models.CharField(unique=True, max_length=16)
    course_id = models.CharField(db_index=True, max_length=255)
    unique_together = (user, course_id)


def anonymous_id_for_user(user, course_id):
    """
    Return a unique id for a (user, course) pair, suitable for inserting
    into e.g. personalized survey links.

    If user is an `AnonymousUser`, returns `None`
    """
    # This part is for ability to get xblock instance in xblock_noauth handlers, where user is unauthenticated.
    if user.is_anonymous():
        return None

    # include the secret key as a salt, and to make the ids unique across different LMS installs.
    hasher = hashlib.md5()
    hasher.update(settings.SECRET_KEY)
    hasher.update(str(user.id))
    hasher.update(course_id)

    return AnonymousUserId.objects.get_or_create(
        defaults={'anonymous_user_id': hasher.hexdigest()},
        user=user,
        course_id=course_id
    )[0].anonymous_user_id


def user_by_anonymous_id(id):
    """
    Return user by anonymous_user_id using AnonymousUserId lookup table.

    Do not raise `django.ObjectDoesNotExist` exception,
    if there is no user for anonymous_student_id,
    because this function will be used inside xmodule w/o django access.
    """

    if id is None:
        return None

    try:
        return User.objects.get(anonymoususerid__anonymous_user_id=id)
    except ObjectDoesNotExist:
        return None


class UserStanding(models.Model):
    """
    This table contains a student's account's status.
    Currently, we're only disabling accounts; in the future we can imagine
    taking away more specific privileges, like forums access, or adding
    more specific karma levels or probationary stages.
    """
    ACCOUNT_DISABLED = "disabled"
    ACCOUNT_ENABLED = "enabled"
    USER_STANDING_CHOICES = (
        (ACCOUNT_DISABLED, u"Account Disabled"),
        (ACCOUNT_ENABLED, u"Account Enabled"),
    )

    user = models.ForeignKey(User, db_index=True, related_name='standing', unique=True)
    account_status = models.CharField(
        blank=True, max_length=31, choices=USER_STANDING_CHOICES
    )
    changed_by = models.ForeignKey(User, blank=True)
    standing_last_changed_at = models.DateTimeField(auto_now=True)


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

    # CRITICAL TODO/SECURITY
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
    this_year = datetime.now(UTC).year
    VALID_YEARS = range((this_year-settings.DELTA_YEAR), this_year - settings.MAX_YEAR_ALLOWED, -1)
    year_of_birth = models.IntegerField(blank=True, null=True, db_index=True)
    GENDER_CHOICES = (('m', _('Male')), ('f', _('Female')), ('o', _('Other')))
    gender = models.CharField(
        blank=True, null=True, max_length=6, db_index=True, choices=GENDER_CHOICES
    )

    # [03/21/2013] removed these, but leaving comment since there'll still be
    # p_se and p_oth in the existing data in db.
    # ('p_se', 'Doctorate in science or engineering'),
    # ('p_oth', 'Doctorate in another field'),
    LEVEL_OF_EDUCATION_CHOICES = (
        ('p', _('Doctorate')),
        ('m', _("Master's or professional degree")),
        ('b', _("Bachelor's degree")),
        ('a', _("Associate's degree")),
        ('hs', _("Secondary/high school")),
        ('jhs', _("Junior secondary/junior high/middle school")),
        ('el', _("Elementary/primary school")),
        ('none', _("None")),
        ('other', _("Other"))
    )
    level_of_education = models.CharField(
        blank=True, null=True, max_length=6, db_index=True,
        choices=LEVEL_OF_EDUCATION_CHOICES
    )
    mailing_address = models.TextField(blank=True, null=True)
    goals = models.TextField(blank=True, null=True)
    allow_certificate = models.BooleanField(default=1)
    #EVEX fields
    cedula = models.CharField(max_length=32, blank=True, null=True)
    city = models.ForeignKey(City, default=None, blank=True, null=True)

    def get_meta(self):
        js_str = self.meta
        if not js_str:
            js_str = dict()
        else:
            js_str = json.loads(self.meta)

        return js_str

    def set_meta(self, js):
        self.meta = json.dumps(js)


def unique_id_for_user(user):
    """
    Return a unique id for a user, suitable for inserting into
    e.g. personalized survey links.
    """
    # Setting course_id to '' makes it not affect the generated hash,
    # and thus produce the old per-student anonymous id
    return anonymous_id_for_user(user, '')


# TODO: Should be renamed to generic UserGroup, and possibly
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


class PendingNameChange(models.Model):
    user = models.OneToOneField(User, unique=True, db_index=True)
    new_name = models.CharField(blank=True, max_length=255)
    rationale = models.CharField(blank=True, max_length=1024)


class PendingEmailChange(models.Model):
    user = models.OneToOneField(User, unique=True, db_index=True)
    new_email = models.CharField(blank=True, max_length=255, db_index=True)
    activation_key = models.CharField(('activation key'), max_length=32, unique=True, db_index=True)



EVENT_NAME_ENROLLMENT_ACTIVATED = 'edx.course.enrollment.activated'
EVENT_NAME_ENROLLMENT_DEACTIVATED = 'edx.course.enrollment.deactivated'


class CourseEnrollment(models.Model):
    """
    Represents a Student's Enrollment record for a single Course. You should
    generally not manipulate CourseEnrollment objects directly, but use the
    classmethods provided to enroll, unenroll, or check on the enrollment status
    of a given student.

    We're starting to consolidate course enrollment logic in this class, but
    more should be brought in (such as checking against CourseEnrollmentAllowed,
    checking course dates, user permissions, etc.) This logic is currently
    scattered across our views.
    """
    user = models.ForeignKey(User)
    course_id = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)

    # If is_active is False, then the student is not considered to be enrolled
    # in the course (is_enrolled() will return False)
    is_active = models.BooleanField(default=True)

    # Represents the modes that are possible. We'll update this later with a
    # list of possible values.
    mode = models.CharField(default="honor", max_length=100)


    class Meta:
        unique_together = (('user', 'course_id'),)
        ordering = ('user', 'course_id')

    def __unicode__(self):
        return (
            "[CourseEnrollment] {}: {} ({}); active: ({})"
        ).format(self.user, self.course_id, self.created, self.is_active)

    @classmethod
    def get_or_create_enrollment(cls, user, course_id):
        """
        Create an enrollment for a user in a class. By default *this enrollment
        is not active*. This is useful for when an enrollment needs to go
        through some sort of approval process before being activated. If you
        don't need this functionality, just call `enroll()` instead.

        Returns a CoursewareEnrollment object.

        `user` is a Django User object. If it hasn't been saved yet (no `.id`
               attribute), this method will automatically save it before
               adding an enrollment for it.

        `course_id` is our usual course_id string (e.g. "edX/Test101/2013_Fall")

        It is expected that this method is called from a method which has already
        verified the user authentication and access.
        """
        # If we're passing in a newly constructed (i.e. not yet persisted) User,
        # save it to the database so that it can have an ID that we can throw
        # into our CourseEnrollment object. Otherwise, we'll get an
        # IntegrityError for having a null user_id.
        if user.id is None:
            user.save()

        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=user,
            course_id=course_id,
        )

        # If we *did* just create a new enrollment, set some defaults
        if created:
            enrollment.mode = "honor"
            enrollment.is_active = False
            enrollment.save()

        return enrollment

    def update_enrollment(self, mode=None, is_active=None):
        """
        Updates an enrollment for a user in a class.  This includes options
        like changing the mode, toggling is_active True/False, etc.

        Also emits relevant events for analytics purposes.

        This saves immediately.
        """
        activation_changed = False
        # if is_active is None, then the call to update_enrollment didn't specify
        # any value, so just leave is_active as it is
        if self.is_active != is_active and is_active is not None:
            self.is_active = is_active
            activation_changed = True

        mode_changed = False
        # if mode is None, the call to update_enrollment didn't specify a new
        # mode, so leave as-is
        if self.mode != mode and mode is not None:
            self.mode = mode
            mode_changed = True

        if activation_changed or mode_changed:
            self.save()
        if activation_changed:
            if self.is_active:
                self.emit_event(EVENT_NAME_ENROLLMENT_ACTIVATED)
            else:
                unenroll_done.send(sender=None, course_enrollment=self)
                self.emit_event(EVENT_NAME_ENROLLMENT_DEACTIVATED)

    def emit_event(self, event_name):
        """
        Emits an event to explicitly track course enrollment and unenrollment.
        """

        try:
            context = contexts.course_context_from_course_id(self.course_id)
            data = {
                'user_id': self.user.id,
                'course_id': self.course_id,
                'mode': self.mode,
            }

            with tracker.get_tracker().context(event_name, context):
                server_track(crum.get_current_request(), event_name, data)
        except:  # pylint: disable=bare-except
            if event_name and self.course_id:
                log.exception('Unable to emit event %s for user %s and course %s', event_name, self.user.username, self.course_id)

    @classmethod
    def enroll(cls, user, course_id, mode="honor"):
        """
        Enroll a user in a course. This saves immediately.

        Returns a CoursewareEnrollment object.

        `user` is a Django User object. If it hasn't been saved yet (no `.id`
               attribute), this method will automatically save it before
               adding an enrollment for it.

        `course_id` is our usual course_id string (e.g. "edX/Test101/2013_Fall")

        `mode` is a string specifying what kind of enrollment this is. The
               default is "honor", meaning honor certificate. Future options
               may include "audit", "verified_id", etc. Please don't use it
               until we have these mapped out.

        It is expected that this method is called from a method which has already
        verified the user authentication and access.
        """
        enrollment = cls.get_or_create_enrollment(user, course_id)
        enrollment.update_enrollment(is_active=True, mode=mode)
        return enrollment

    @classmethod
    def enroll_by_email(cls, email, course_id, mode="honor", ignore_errors=True):
        """
        Enroll a user in a course given their email. This saves immediately.

        Note that  enrolling by email is generally done in big batches and the
        error rate is high. For that reason, we supress User lookup errors by
        default.

        Returns a CoursewareEnrollment object. If the User does not exist and
        `ignore_errors` is set to `True`, it will return None.

        `email` Email address of the User to add to enroll in the course.

        `course_id` is our usual course_id string (e.g. "edX/Test101/2013_Fall")

        `mode` is a string specifying what kind of enrollment this is. The
               default is "honor", meaning honor certificate. Future options
               may include "audit", "verified_id", etc. Please don't use it
               until we have these mapped out.

        `ignore_errors` is a boolean indicating whether we should suppress
                        `User.DoesNotExist` errors (returning None) or let it
                        bubble up.

        It is expected that this method is called from a method which has already
        verified the user authentication and access.
        """
        try:
            user = User.objects.get(email=email)
            return cls.enroll(user, course_id, mode)
        except User.DoesNotExist:
            err_msg = u"Tried to enroll email {} into course {}, but user not found"
            log.error(err_msg.format(email, course_id))
            if ignore_errors:
                return None
            raise

    @classmethod
    def unenroll(cls, user, course_id):
        """
        Remove the user from a given course. If the relevant `CourseEnrollment`
        object doesn't exist, we log an error but don't throw an exception.

        `user` is a Django User object. If it hasn't been saved yet (no `.id`
               attribute), this method will automatically save it before
               adding an enrollment for it.

        `course_id` is our usual course_id string (e.g. "edX/Test101/2013_Fall")
        """
        try:
            record = CourseEnrollment.objects.get(user=user, course_id=course_id)
            record.update_enrollment(is_active=False)

        except cls.DoesNotExist:
            err_msg = u"Tried to unenroll student {} from {} but they were not enrolled"
            log.error(err_msg.format(user, course_id))

    @classmethod
    def unenroll_by_email(cls, email, course_id):
        """
        Unenroll a user from a course given their email. This saves immediately.
        User lookup errors are logged but will not throw an exception.

        `email` Email address of the User to unenroll from the course.

        `course_id` is our usual course_id string (e.g. "edX/Test101/2013_Fall")
        """
        try:
            user = User.objects.get(email=email)
            return cls.unenroll(user, course_id)
        except User.DoesNotExist:
            err_msg = u"Tried to unenroll email {} from course {}, but user not found"
            log.error(err_msg.format(email, course_id))

    @classmethod
    def is_enrolled(cls, user, course_id):
        """
        Returns True if the user is enrolled in the course (the entry must exist
        and it must have `is_active=True`). Otherwise, returns False.

        `user` is a Django User object. If it hasn't been saved yet (no `.id`
               attribute), this method will automatically save it before
               adding an enrollment for it.

        `course_id` is our usual course_id string (e.g. "edX/Test101/2013_Fall")
        """
        try:
            record = CourseEnrollment.objects.get(user=user, course_id=course_id)
            return record.is_active
        except cls.DoesNotExist:
            return False

    @classmethod
    def is_enrolled_by_partial(cls, user, course_id_partial):
        """
        Returns `True` if the user is enrolled in a course that starts with
        `course_id_partial`. Otherwise, returns False.

        Can be used to determine whether a student is enrolled in a course
        whose run name is unknown.

        `user` is a Django User object. If it hasn't been saved yet (no `.id`
               attribute), this method will automatically save it before
               adding an enrollment for it.

        `course_id_partial` is a starting substring for a fully qualified
               course_id (e.g. "edX/Test101/").
        """
        try:
            return CourseEnrollment.objects.filter(
                user=user,
                course_id__startswith=course_id_partial,
                is_active=1
            ).exists()
        except cls.DoesNotExist:
            return False

    @classmethod
    def enrollment_mode_for_user(cls, user, course_id):
        """
        Returns the enrollment mode for the given user for the given course

        `user` is a Django User object
        `course_id` is our usual course_id string (e.g. "edX/Test101/2013_Fall")
        """
        try:
            record = CourseEnrollment.objects.get(user=user, course_id=course_id)
            if record.is_active:
                return record.mode
            else:
                return None
        except cls.DoesNotExist:
            return None

    @classmethod
    def enrollments_for_user(cls, user):
        return CourseEnrollment.objects.filter(user=user, is_active=1)

    @classmethod
    def users_enrolled_in(cls, course_id):
        """Return a queryset of User for every user enrolled in the course."""
        return User.objects.filter(
            courseenrollment__course_id=course_id,
            courseenrollment__is_active=True
        )

    def activate(self):
        """Makes this `CourseEnrollment` record active. Saves immediately."""
        self.update_enrollment(is_active=True)

    def deactivate(self):
        """Makes this `CourseEnrollment` record inactive. Saves immediately. An
        inactive record means that the student is not enrolled in this course.
        """
        self.update_enrollment(is_active=False)

    def change_mode(self, mode):
        """Changes this `CourseEnrollment` record's mode to `mode`.  Saves immediately."""
        self.update_enrollment(mode=mode)

    def refundable(self):
        """
        For paid/verified certificates, students may receive a refund IFF they have
        a verified certificate and the deadline for refunds has not yet passed.
        """
        course_mode = CourseMode.mode_for_course(self.course_id, 'verified')
        if course_mode is None:
            return False
        else:
            return True


class CourseEnrollmentAllowed(models.Model):
    """
    Table of users (specified by email address strings) who are allowed to enroll in a specified course.
    The user may or may not (yet) exist.  Enrollment by users listed in this table is allowed
    even if the enrollment time window is past.
    """
    email = models.CharField(max_length=255, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)
    auto_enroll = models.BooleanField(default=0)

    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)

    class Meta:
        unique_together = (('email', 'course_id'),)

    def __unicode__(self):
        return "[CourseEnrollmentAllowed] %s: %s (%s)" % (self.email, self.course_id, self.created)

# cache_relation(User.profile)

#### Helper methods for use from python manage.py shell and other classes.


def get_user_by_username_or_email(username_or_email):
    """
    Return a User object, looking up by email if username_or_email contains a
    '@', otherwise by username.

    Raises:
        User.DoesNotExist is lookup fails.
    """
    if '@' in username_or_email:
        return User.objects.get(email=username_or_email)
    else:
        return User.objects.get(username=username_or_email)


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
    if not settings.MITX_FEATURES['ENABLE_DISCUSSION_SERVICE']:
        # Don't try--it won't work, and it will fill the logs with lots of errors
        return
    try:
        cc_user = cc.User.from_django_user(instance)
        cc_user.save()
    except Exception as e:
        log = logging.getLogger("mitx.discussion")
        log.error(unicode(e))
        log.error("update user info to discussion failed for user with id: " + str(instance.id))

# Define login and logout handlers here in the models file, instead of the views file,
# so that they are more likely to be loaded when a Studio user brings up the Studio admin
# page to login.  These are currently the only signals available, so we need to continue
# identifying and logging failures separately (in views).


@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """Handler to log when logins have occurred successfully."""
    AUDIT_LOG.info(u"Login success - {0} ({1})".format(user.username, user.email))


@receiver(user_logged_out)
def log_successful_logout(sender, request, user, **kwargs):
    """Handler to log when logouts have occurred successfully."""
    AUDIT_LOG.info(u"Logout - {0}".format(request.user))
