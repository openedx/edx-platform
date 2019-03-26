from bridgekeeper import perms
from bridgekeeper.rules import is_staff, Attribute, Rule, blanket_rule, UNIVERSAL, EMPTY, is_authenticated
from django.conf import settings
from openedx.features.course_experience import COURSE_PRE_START_ACCESS_FLAG
from courseware import access_utils
from django.db.models import Q, F, Subquery
from datetime import datetime
from pytz import UTC
from student.models import CourseEnrollmentAllowed, CourseAccessRole
from student.roles import (
    CourseStaffRole, CourseInstructorRole, OrgStaffRole, OrgInstructorRole, CourseBetaTesterRole
)
from courseware.masquerade import is_masquerading_as_student
from xmodule.course_module import CATALOG_VISIBILITY_CATALOG_AND_ABOUT


class IsMasqueradingAsStudent(Rule):
    def query(self, user):
        return Q(id__in=(
            course_id
            for (course_id, masq)
            in getattr(user, 'masquerade_settings', {}).items()
            if masq.role == 'student'
        ))
    def check(self, user, instance=None):
        if instance is None:
            return False
        return is_masquerading_as_student(user, instance.id)

class AfterStartDate(Rule):
    def query(self, user):

        if COURSE_PRE_START_ACCESS_FLAG.is_enabled():
            return UNIVERSAL

        start_dates_disabled = settings.FEATURES['DISABLE_START_DATES']
        if start_dates_disabled:
            masquerading_as_student = IsMasqueradingAsStudent().query(user)
            return ~masquerading_as_student

        if access_utils.in_preview_mode():
            return UNIVERSAL

        is_masquerading = Q(id__in=(getattr(user, 'masquerade_settings', {}).keys()))
        start_is_none = Q(start=None)

        now = datetime.now(UTC)

        if user.is_authenticated:
            beta_role_ids = user.courseaccessrole_set.filter(role=CourseBetaTesterRole.ROLE).values('course_id')
            beta_test_courses = Q(id__in=Subquery(beta_role_ids))
            non_beta_start_is_passed=Q(start__lt=now) & (~beta_test_courses | Q(days_early_for_beta=None))
            beta_start_is_passed=Q(start__lt=now+F('days_early_for_beta')) & beta_test_courses

            return is_masquerading | start_is_none | non_beta_start_is_passed | beta_start_is_passed
        else:
            return start_is_none

    def check(self, user, instance=None):
        if instance is None:
            return False

        return access_utils.check_course_open_for_learner(user, instance)


class HasCourseEnrollmentAllowed(Rule):
    def query(self, user):
        if user is None or not user.is_authenticated:
            return EMPTY

        return Q(id__in=CourseEnrollmentAllowed.objects.filter(
            Q(email=user.email) & (Q(user__isnull=True) | Q(user_id=user.id))
        ).values('course_id'))

    def check(self, user, instance=None):
        if instance is None:
            return False

        if user is not None and user.is_authenticated:
            cea = CourseEnrollmentAllowed.objects.filter(email=user.email, course_id=instance.id).first()
            return cea and cea.valid_for_user(user)


class InEnrollmentPeriod(Rule):
    def query(self, user):
        now = datetime.now(UTC)
        start_query = Q(enrollment_start__lt=now) | Q(enrollment_start__isnull=True)
        end_query = Q(enrollment_end__gt=now) | Q(enrollment_end__isnull=True)
        return (start_query & end_query)

    def check(self, user, instance=None):
        if instance is None:
            return False

        now = datetime.now(UTC)
        enrollment_start = instance.enrollment_start or datetime.min.replace(tzinfo=UTC)
        enrollment_end = instance.enrollment_end or datetime.max.replace(tzinfo=UTC)
        return enrollment_start < now < enrollment_end


class HasStaffAccess(Rule):
    def query(self, user):
        courses_with_staff_access = CourseAccessRole.objects.filter(
            role=CourseStaffRole.ROLE, user=user
        ).values('course_id')

        orgs_with_staff_access = CourseAccessRole.objects.filter(
            Q(role=OrgStaffRole.ROLE, user=user) & Q(course_id=CourseAccessRole._meta.get_field('course_id').Empty)
        ).values('course_id')

        return Q(id__in=Subquery(courses_with_staff_access)) | Q(org__in=Subquery(orgs_with_staff_access))

    def check(self, user, instance=None):
        if instance is None:
            return False

        return (
            CourseStaffRole(instance.id).has_user(user) or
            OrgStaffRole(instance.org).has_user(user)
        )


class HasInstructorAccess(Rule):
    def query(self, user):
        courses_with_staff_access = CourseAccessRole.objects.filter(
            role=CourseInstructorRole.ROLE, user=user
        ).values('course_id')

        orgs_with_staff_access = CourseAccessRole.objects.filter(
            Q(role=OrgInstructorRole.ROLE, user=user) & Q(course_id=CourseAccessRole._meta.get_field('course_id').Empty)
        ).values('course_id')

        return Q(id__in=Subquery(courses_with_staff_access)) | Q(org__in=Subquery(orgs_with_staff_access))

    def check(self, user, instance=None):
        if instance is None:
            return False

        return (
            CourseInstructorRole(instance.id).has_user(user) or
            OrgInstructorRole(instance.org).has_user(user)
        )

visible_to_nonstaff_users = Attribute('visible_to_staff_only', False)
course_start_unset = Attribute('start', None)


@blanket_rule
def in_preview_mode(user):
    return access_utils.in_preview_mode()

course_open_for_learner = AfterStartDate()

@blanket_rule
def prereqs_disabled(user):
    return not is_prerequisite_courses_enabled()

is_staff_in_course = is_authenticated & (~IsMasqueradingAsStudent()) & (is_staff | HasStaffAccess() | HasInstructorAccess())
invitation_only = Attribute('invitation_only', True)


passed_prerequisites = prereqs_disabled | is_staff_in_course

has_catalog_visibility = Attribute('catalog_visibility', CATALOG_VISIBILITY_CATALOG_AND_ABOUT)

perms['courseware.see_in_catalog'] = is_staff_in_course | has_catalog_visibility

perms['courseware.can_load'] = is_staff | (
    visible_to_nonstaff_users &
    course_open_for_learner # &
    # passed_prerequisites
    # course_not_expired
)
perms['courseware.can_enroll'] = HasCourseEnrollmentAllowed() | is_staff_in_course | (~invitation_only) & InEnrollmentPeriod()
perms['courseware.see_exists'] = perms['courseware.can_load'] | perms['courseware.can_enroll']
