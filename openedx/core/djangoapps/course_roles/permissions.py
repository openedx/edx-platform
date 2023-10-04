"""
Permissions for course roles app.
"""
from enum import Enum, unique

from django.utils.translation import ugettext as _


@unique
class CourseRolesPermission(Enum):
    """
    Enum of all user permissions, the values are the permissions names
    in the course_roles_permission table in database.
    """
    MANAGE_CONTENT = "manage_content"
    MANAGE_COURSE_SETTINGS = "manage_course_settings"
    MANAGE_ADVANCED_SETTINGS = "manage_advanced_settings"
    VIEW_COURSE_SETTINGS = "view_course_settings"
    VIEW_ALL_CONTENT = "view_all_content"
    VIEW_ONLY_LIVE_PUBLISHED_CONTENT = "view_only_live_published_content"
    VIEW_ALL_PUBLISHED_CONTENT = "view_all_published_content"
    ACCESS_INSTRUCTOR_DASHBOARD = "access_instructor_dashboard"
    ACCESS_DATA_DOWNLOADS = "access_data_downloads"
    MANAGE_GRADES = "manage_grades"
    VIEW_GRADEBOOK = "view_gradebook"
    MANAGE_ALL_USERS = "manage_all_users"
    MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF = "manage_users_except_admin_and_staff"
    MANAGE_DISCUSSION_MODERATORS = "manage_discussion_moderators"
    MANAGE_COHORTS = "manage_cohorts"
    MANAGE_STUDENTS = "manage_students"
    MODERATE_DISCUSSION_FORUMS = "moderate_discussion_forums"
    MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT = "moderate_discussion_forums_for_a_cohort"
    MANAGE_CERTIFICATES = "manage_certificates"
    MANAGE_LIBRARIES = "manage_libraries"
    GENERAL_MASQUERADING = "general_masquerading"
    SPECIFIC_MASQUERADING = "specific_masquerading"


course_roles_permissions = {
    CourseRolesPermission.MANAGE_CONTENT: {
        "name": _("Manage Content"),
        "description": _("Can view, create, edit, delete and publish (not publisher tool) any course content."),
    },
    CourseRolesPermission.MANAGE_COURSE_SETTINGS: {
        "name": _("Manage Course Settings"),
        "description": _("Can view and edit settings pages."),
    },
    CourseRolesPermission.MANAGE_ADVANCED_SETTINGS: {
        "name": _("Manage Advanced Settings"),
        "description": _("Can view and edit advanced settings."),
    },
    CourseRolesPermission.VIEW_COURSE_SETTINGS: {
        "name": _("View Course Settings"),
        "description": _("Can view all settings pages."),
    },
    CourseRolesPermission.VIEW_ALL_CONTENT: {
        "name": _("View All Content"),
        "description": _(
            "Can view course content in LMS in all statuses: "
            "Published and live, Draft, Staff-only, Published-not-yet-released."
        ),
    },
    CourseRolesPermission.VIEW_ONLY_LIVE_PUBLISHED_CONTENT: {
        "name": _("View Only Live Published Content"),
        "description": _(
            "Can only view published-and-live content in a course. "
            "Cannot view published-not-yet-released content. Cannot view Staff-only content."
        ),
    },
    CourseRolesPermission.VIEW_ALL_PUBLISHED_CONTENT: {
        "name": _("View All Published Content"),
        "description": _("Can view all Published content, including published-not-yet-released."),
    },
    CourseRolesPermission.ACCESS_INSTRUCTOR_DASHBOARD: {
        "name": _("Access Instructor Dashboard"),
        "description": _("Can view Instructor Dashboard with Basic Course Information."),
    },
    CourseRolesPermission.ACCESS_DATA_DOWNLOADS: {
        "name": _("Access Data Downloads"),
        "description": _("Can view Data Downloads tab and generate all report types."),
    },
    CourseRolesPermission.MANAGE_GRADES: {
        "name": _("Manage Grades"),
        "description": _("Can view and edit grades in Student Admin tab, Gradebook, and Open Responses."),
    },
    CourseRolesPermission.VIEW_GRADEBOOK: {
        "name": _("View Gradebook"),
        "description": _("Can view gradebook but cannot download or edit anything."),
    },
    CourseRolesPermission.MANAGE_ALL_USERS: {
        "name": _("Manage All Users"),
        "description": _("Can add, remove, and change role for all members of the course team."),
    },
    CourseRolesPermission.MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF: {
        "name": _("Manage Users Except Admin and Staff"),
        "description": _("Can add, remove, change role for members of the course team, EXCEPT Admins and Staff."),
    },
    CourseRolesPermission.MANAGE_DISCUSSION_MODERATORS: {
        "name": _("Manage Discussion Moderators"),
        "description": _("Can add and remove all moderator roles."),
    },
    CourseRolesPermission.MANAGE_COHORTS: {
        "name": _("Manage Cohorts"),
        "description": _("Can add and remove learners in cohorts; Can add new cohorts."),
    },
    CourseRolesPermission.MANAGE_STUDENTS: {
        "name": _("Manage Students"),
        "description": _(
            "Can manage batch enrollments of audit learners and beta testers; Can manage cohorts, "
            "extensions, student admin, Insights, bulk email, special exams, and open responses."
        ),
    },
    CourseRolesPermission.MODERATE_DISCUSSION_FORUMS: {
        "name": _("Moderate Discussion Forums"),
        "description": _(
            "Can view, edit, or delete all posts; Can pin, close, or reopen posts; "
            "Can endorse responses, reports/flags."
        ),
    },
    CourseRolesPermission.MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT: {
        "name": _("Moderate Discussion Forums for a Cohort"),
        "description": _(
            "Can view, edit, or delete all posts; Can pin, close, or reopen posts; Can endorse responses, "
            "reports/flags. (Limited to user's own cohort)."
        ),
    },
    CourseRolesPermission.MANAGE_CERTIFICATES: {
        "name": _("Manage Certificates"),
        "description": _("Can generate, regenerate, make exceptions, and invalidate certificates."),
    },
    CourseRolesPermission.MANAGE_LIBRARIES: {
        "name": _("Manage Libraries"),
        "description": _("Can create and edit content libraries; Can pull in content libraries via Content Outline."),
    },
    CourseRolesPermission.GENERAL_MASQUERADING: {
        "name": _("General Masquerading"),
        "description": _("Can view the course as an Audit or Verified learner only."),
    },
    CourseRolesPermission.SPECIFIC_MASQUERADING: {
        "name": _("Specific Masquerading"),
        "description": _("Can view the course as an Audit, Verified, Beta Tester, Masters track, username/email."),
    },
}
