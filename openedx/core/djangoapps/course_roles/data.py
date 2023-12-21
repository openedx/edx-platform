"""
Permissions for course roles app.

These are the permissions that can be assigned to a CourseRole which grants access for a course,
but can also be assigned for org wide course access or instance wide course access.
They are defined in the database in the course_roles_permission table.

Remember that edX has blue/green deployments, so they're going to be running in a state
where some of the code has the new permissions and some won't.
So old code needs to be resilient to seeing new permissions it doesn't recognize.

To add a new permission, add a new entry to the CourseRolesPermission enum,
then and add a new row to the course_roles_permission table in database,
with a migration in this app.

To remove a permission, remove the entry from the CourseRolesPermission enum,
and remove the row from the course_roles_permission table in database,
with a migration in this app.

To change the readable_name or description of a permission, change the
corresponding entry in CourseRolesPermission enum.

To change the name of a permission, change the corresponding entry on the
CourseRolesPermission enum, and change the name field of the corresponding
row in the course_roles_permission table in database, with a migration in this app.
"""
from attrs import frozen, field, validators
from enum import Enum, unique

from django.utils.translation import gettext as _


@frozen
class PermissionData:
    """
    Data class for a permission.
    """
    name: str = field(validator=validators.instance_of(str))
    readable_name: str = field(validator=validators.instance_of(str))
    description: str = field(validator=validators.instance_of(str))


@unique
class CourseRolesPermission(Enum):
    """
    Enum of all user permissions, the values are the permissions names
    in the course_roles_permission table in database.

    The readable_name and description are used in the UI.
    """

    MANAGE_CONTENT = PermissionData(
        "manage_content",
        _("Manage Content"),
        _("Can view, create, edit, delete and publish (not publisher tool) any course content."),
    )
    MANAGE_COURSE_SETTINGS = PermissionData(
        "manage_course_settings", _("Manage Course Settings"), _("Can view and edit settings pages.")
    )
    MANAGE_ADVANCED_SETTINGS = PermissionData(
        "manage_advanced_settings", _("Manage Advanced Settings"), _("Can view and edit advanced settings.")
    )
    VIEW_COURSE_SETTINGS = PermissionData(
        "view_course_settings", _("View Course Settings"), _("Can view all settings pages.")
    )
    VIEW_ALL_CONTENT = PermissionData(
        "view_all_content",
        _("View All Content"),
        _(
            "Can view course content in LMS in all statuses: "
            "Published and live, Draft, Staff-only, Published-not-yet-released."
        ),
    )
    VIEW_LIVE_PUBLISHED_CONTENT = PermissionData(
        "view_live_published_content",
        _("View Live Published Content"),
        _(
            "Can view published-and-live content in a course. "
            "Cannot view published-not-yet-released content. Cannot view Staff-only content."
        ),
    )
    VIEW_ALL_PUBLISHED_CONTENT = PermissionData(
        "view_all_published_content",
        _("View All Published Content"),
        _("Can view all Published content, including published-not-yet-released."),
    )
    ACCESS_INSTRUCTOR_DASHBOARD = PermissionData(
        "access_instructor_dashboard",
        _("Access Instructor Dashboard"),
        _("Can view Instructor Dashboard with Basic Course Information."),
    )
    ACCESS_DATA_DOWNLOADS = PermissionData(
        "access_data_downloads",
        _("Access Data Downloads"),
        _("Can view Data Downloads tab and generate all report types."),
    )
    MANAGE_GRADES = PermissionData(
        "manage_grades",
        _("Manage Grades"),
        _("Can view and edit grades in Student Admin tab, Gradebook, and Open Responses."),
    )
    VIEW_GRADEBOOK = PermissionData(
        "view_gradebook", _("View Gradebook"), _("Can view gradebook but cannot download or edit anything.")
    )
    MANAGE_ALL_USERS = PermissionData(
        "manage_all_users",
        _("Manage All Users"),
        _("Can add, remove, and change role for all members of the course team."),
    )
    MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF = PermissionData(
        "manage_users_except_admin_and_staff",
        _("Manage Users Except Admin and Staff"),
        _("Can add, remove, change role for members of the course team, EXCEPT Admins and Staff."),
    )
    MANAGE_DISCUSSION_MODERATORS = PermissionData(
        "manage_discussion_moderators", _("Manage Discussion Moderators"), _("Can add and remove all moderator roles.")
    )
    MANAGE_COHORTS = PermissionData(
        "manage_cohorts", _("Manage Cohorts"), _("Can add and remove learners in cohorts; Can add new cohorts.")
    )
    MANAGE_STUDENTS = PermissionData(
        "manage_students",
        _("Manage Students"),
        _(
            "Can manage batch enrollments of audit learners and beta testers; Can manage cohorts, "
            "extensions, student admin, Insights, bulk email, special exams, and open responses."
        ),
    )
    MODERATE_DISCUSSION_FORUMS = PermissionData(
        "moderate_discussion_forums",
        _("Moderate Discussion Forums"),
        _(
            "Can view, edit, or delete all posts; Can pin, close, or reopen posts; "
            "Can endorse responses, reports/flags."
        ),
    )
    MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT = PermissionData(
        "moderate_discussion_forums_for_a_cohort",
        _("Moderate Discussion Forums for a Cohort"),
        _(
            "Can view, edit, or delete all posts; Can pin, close, or reopen posts; Can endorse responses, "
            "reports/flags. (Limited to user's own cohort)."
        ),
    )
    MANAGE_CERTIFICATES = PermissionData(
        "manage_certificates",
        _("Manage Certificates"),
        _("Can generate, regenerate, make exceptions, and invalidate certificates."),
    )
    MANAGE_LIBRARIES = PermissionData(
        "manage_libraries",
        _("Manage Libraries"),
        _("Can create and edit content libraries; Can pull in content libraries via Content Outline."),
    )
    GENERAL_MASQUERADING = PermissionData(
        "general_masquerading",
        _("General Masquerading"),
        _("Can view the course as an Audit or Verified learner only."),
    )
    SPECIFIC_MASQUERADING = PermissionData(
        "specific_masquerading",
        _("Specific Masquerading"),
        _("Can view the course as an Audit, Verified, Beta Tester, Master's track, username/email."),
    )

    @property
    def perm_name(self):
        """
        The permission name with the course_roles prefix.
        Example: course_roles.manage_content
        """
        return f'course_roles.{self.value.name}'
