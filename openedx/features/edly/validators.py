from logging import getLogger

from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext as _

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.features.edly.constants import (
    ESSENTIALS,
    NUMBER_OF_COURSES,
    NUMBER_OF_REGISTERED_USERS,
)
from openedx.features.edly.models import (
    EdlySubOrganization,
    EdlyUserProfile
)
from openedx.features.edly.utils import (
    create_user_link_with_edly_sub_organization,
    user_can_login_on_requested_edly_organization
)
from student.models import User

logger = getLogger(__name__)


def is_edly_user_allowed_to_login(request, possibly_authenticated_user):
    """
    Check if the user is allowed to login on the current site.

    This method checks if the user has edly sub organization of current
    site in it's edly sub organizations list.

    Arguments:
        request (object): HTTP request object
        possibly_authenticated_user (User): User object trying to authenticate

    Returns:
        bool: Returns True if User has Edly Sub Organization Access Otherwise False.
    """

    if possibly_authenticated_user.is_superuser:
        return True

    try:
        edly_sub_org = request.site.edly_sub_org_for_lms
    except EdlySubOrganization.DoesNotExist:
        logger.error('Edly sub organization does not exist for site %s.' % request.site)
        return False

    try:
        edly_user_profile = possibly_authenticated_user.edly_profile
    except EdlyUserProfile.DoesNotExist:
        logger.warning('User %s has no edly profile for site %s.' % (possibly_authenticated_user.email, request.site))
        return False

    if edly_sub_org.slug in edly_user_profile.get_linked_edly_sub_organizations:
        return True

    return False


def is_edly_user_allowed_to_login_with_social_auth(request, user):
    """
    Check if the user is allowed to login on the current site with social auth.

    Arguments:
        request (object): HTTP request object
        user: User object trying to authenticate

    Returns:
        bool: Returns True if User can login to site otherwise False.
    """

    if not is_edly_user_allowed_to_login(request, user):
        if user_can_login_on_requested_edly_organization(request, user):
            create_user_link_with_edly_sub_organization(request, user)
        else:
            logger.warning('User %s is not allowed to login for site %s.' % (user.email, request.site))
            return False

    return True


def is_courses_limit_reached_for_plan():
    """
    Checks if the limit for the current site for number of courses is reached.
    """
    site_config = configuration_helpers.get_current_site_configuration()
    current_plan = site_config.get_value('DJANGO_SETTINGS_OVERRIDE').get('CURRENT_PLAN', ESSENTIALS)
    plan_features = settings.PLAN_FEATURES.get(current_plan)

    courses_count = CourseOverview.get_all_courses(orgs=configuration_helpers.get_current_site_orgs()).count()

    if courses_count >= plan_features.get(NUMBER_OF_COURSES):
        return True

    return False


def is_registered_user_limit_reached_for_plan(request):
    """
    Checks if the limit for the current site for number of registered users is reached.
    """
    errors = {}
    try:
        site_config = configuration_helpers.get_current_site_configuration()
        current_plan = site_config.get_value('DJANGO_SETTINGS_OVERRIDE').get('CURRENT_PLAN', ESSENTIALS)
        plan_features = settings.PLAN_FEATURES.get(current_plan)

        user_records_count = User.objects.select_related('profile').select_related('edly_profile').exclude(
            groups__name=settings.ADMIN_CONFIGURATION_USERS_GROUP
        ).filter(
            Q(edly_profile__edly_sub_organizations=request.site.edly_sub_org_for_lms)
        ).count()

        if user_records_count >= plan_features.get(NUMBER_OF_REGISTERED_USERS):
            errors['email'] = [{"user_message": _(
                u"The maximum courses limit for your plan has reached. "
                u"Please upgrade your plan."
                )}]
            return errors

        return False

    except AttributeError:
        return False
