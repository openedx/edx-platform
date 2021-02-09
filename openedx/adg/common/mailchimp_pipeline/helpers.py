"""
Helper methods for Mailchimp pipeline
"""
from common.djangoapps.student.models import CourseEnrollment, UserProfile
from openedx.adg.constants import MONTH_DAY_YEAR_FORMAT


def get_enrollment_course_names_and_short_ids_by_user(user):
    """
    Get comma separated course names and short ids, for all enrolled courses.

    Args:
        user (user object): User model object

    Returns:
        Tuple of comma separated course short ids and course names
    """
    enrollments = CourseEnrollment.enrollments_for_user(user).values_list(
        'course__course_meta__short_id', 'course__display_name'
    )

    if not enrollments:
        return '', ''

    short_ids, display_names = zip(*enrollments)
    return ','.join(map(str, short_ids)), ','.join(display_names)


def is_mailchimp_sync_required(created, sender, **kwargs):
    """
    Checks if sync is required with mailchimp. Sync will be done if `created` is `true`, `sender` is `UserProfile` or
    `update_fields` have one of the fields which is required on mailchimp.

    Args:
        created (bool): True if the object of `sender` class is created
        sender (obj): Class which sent the signal.
        kwargs (dict): Additional Params.

    Returns:
        bool: True if sync is required else False.
    """
    MAILCHIMP_FIELDS = ['organization', 'status', 'business_line', 'company']
    update_fields = kwargs.get('update_fields') or []
    return created or sender == UserProfile or any(field in update_fields for field in MAILCHIMP_FIELDS)


def get_user_merge_fields(user):
    """
    Computes merge_fields for mailchimp using User object.

    Args:
        user (User): User object

    Returns:
        dict: Contains merge fields for a User instance.
    """
    return {'USERNAME': user.username, 'DATEREGIS': str(user.date_joined.strftime(MONTH_DAY_YEAR_FORMAT))}


def get_userprofile_merge_fields(user_profile):
    """
    Computes merge_fields for mailchimp using UserProfile object.

    Args:
        user_profile (UserProfile): UserProfile object

    Returns:
        dict: Contains merge_fields of UserProfile object.
    """
    return {'LOCATION': user_profile.city, 'FULLNAME': user_profile.name}


def get_userapplication_merge_fields(user_application):
    """
    Computes merge_fields for mailchimp using UserApplication object.

    Args:
        user_application (UserApplication): UserAppication object

    Returns:
        dict: Contains merge_fields for UserApplication object.
    """
    return {
        'ORG_NAME': user_application.organization or '',
        'APP_STATUS': user_application.status,
        'B_LINE': user_application.business_line.title if user_application.business_line else ''
    }


def get_extendeduserprofile_merge_fields(extended_profile):
    """
    Computes merge_fields for mailchimp using ExtendedUserProfile object.

    Args:
        extended_profile (ExtendedUserProfile): object of ExtendedUserProfile

    Returns:
        dict: Contains merge_fields for ExtendedUserProfile object.
    """
    return {'COMPANY': extended_profile.company.title if extended_profile.company else ''}
