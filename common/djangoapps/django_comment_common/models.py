import logging

from django.db import models
from django.contrib.auth.models import User

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.translation import ugettext_noop

from student.models import CourseEnrollment

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule_django.models import CourseKeyField, NoneToEmptyManager

FORUM_ROLE_ADMINISTRATOR = ugettext_noop('Administrator')
FORUM_ROLE_MODERATOR = ugettext_noop('Moderator')
FORUM_ROLE_COMMUNITY_TA = ugettext_noop('Community TA')
FORUM_ROLE_STUDENT = ugettext_noop('Student')


@receiver(post_save, sender=CourseEnrollment)
def assign_default_role_on_enrollment(sender, instance, **kwargs):
    """
    Assign forum default role 'Student'
    """
    # The code below would remove all forum Roles from a user when they unenroll
    # from a course. Concerns were raised that it should apply only to students,
    # or that even the history of student roles is important for research
    # purposes. Since this was new functionality being added in this release,
    # I'm just going to comment it out for now and let the forums team deal with
    # implementing the right behavior.
    #
    # # We've unenrolled the student, so remove all roles for this course
    # if not instance.is_active:
    #     course_roles = list(Role.objects.filter(course_id=instance.course_id))
    #     instance.user.roles.remove(*course_roles)
    #     return

    # We've enrolled the student, so make sure they have the Student role
    assign_default_role(instance.course_id, instance.user)


def assign_default_role(course_id, user):
    """
    Assign forum default role 'Student' to user
    """
    role, __ = Role.objects.get_or_create(course_id=course_id, name=FORUM_ROLE_STUDENT)
    user.roles.add(role)


class Role(models.Model):

    objects = NoneToEmptyManager()

    name = models.CharField(max_length=30, null=False, blank=False)
    users = models.ManyToManyField(User, related_name="roles")
    course_id = CourseKeyField(max_length=255, blank=True, db_index=True)

    class Meta(object):
        # use existing table that was originally created from django_comment_client app
        db_table = 'django_comment_client_role'

    def __unicode__(self):
        # pylint: disable=no-member
        return self.name + " for " + (self.course_id.to_deprecated_string() if self.course_id else "all courses")

    # TODO the name of this method is a little bit confusing,
    # since it's one-off and doesn't handle inheritance later
    def inherit_permissions(self, role):
        """
        Make this role inherit permissions from the given role.
        Permissions are only added, not removed. Does not handle inheritance.
        """
        if role.course_id and role.course_id != self.course_id:
            logging.warning(
                "%s cannot inherit permissions from %s due to course_id inconsistency",
                self,
                role,
            )
        for per in role.permissions.all():
            self.add_permission(per)

    def add_permission(self, permission):
        self.permissions.add(Permission.objects.get_or_create(name=permission)[0])

    def has_permission(self, permission):
        """Returns True if this role has the given permission, False otherwise."""
        course = modulestore().get_course(self.course_id)
        if course is None:
            raise ItemNotFoundError(self.course_id)
        if permission_blacked_out(course, {self.name}, permission):
            return False

        return self.permissions.filter(name=permission).exists()


class Permission(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False, primary_key=True)
    roles = models.ManyToManyField(Role, related_name="permissions")

    class Meta(object):
        # use existing table that was originally created from django_comment_client app
        db_table = 'django_comment_client_permission'

    def __unicode__(self):
        return self.name


def permission_blacked_out(course, role_names, permission_name):
    """Returns true if a user in course with the given roles would have permission_name blacked out.

    This will return true if it is a permission that the user might have normally had for the course, but does not have
    right this moment because we are in a discussion blackout period (as defined by the settings on the course module).
    Namely, they can still view, but they can't edit, update, or create anything. This only applies to students, as
    moderators of any kind still have posting privileges during discussion blackouts.
    """
    return (
        not course.forum_posts_allowed and
        role_names == {FORUM_ROLE_STUDENT} and
        any([permission_name.startswith(prefix) for prefix in ['edit', 'update', 'create']])
    )


def all_permissions_for_user_in_course(user, course_id):  # pylint: disable=invalid-name
    """Returns all the permissions the user has in the given course."""
    course = modulestore().get_course(course_id)
    if course is None:
        raise ItemNotFoundError(course_id)

    all_roles = {role.name for role in Role.objects.filter(users=user, course_id=course_id)}

    permissions = {
        permission.name
        for permission
        in Permission.objects.filter(roles__users=user, roles__course_id=course_id)
        if not permission_blacked_out(course, all_roles, permission.name)
    }
    return permissions
