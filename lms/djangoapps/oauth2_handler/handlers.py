""" Handlers for OpenID Connect provider. """

from django.conf import settings
from django.core.cache import cache

from courseware.access import has_access
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.user_api.models import UserPreference
from student.models import anonymous_id_for_user
from student.models import UserProfile
from lang_pref import LANGUAGE_KEY
from student.roles import GlobalStaff, CourseStaffRole, CourseInstructorRole


class OpenIDHandler(object):
    """ Basic OpenID Connect scope handler. """

    def scope_openid(self, _data):
        """ Only override the sub (subject) claim. """
        return ['sub']

    def claim_sub(self, data):
        """
        Return the value of the sub (subject) claim. The value should be
        unique for each user.

        """

        # Use the anonymous ID without any course as unique identifier.
        # Note that this ID is derived using the value of the `SECRET_KEY`
        # setting, this means that users will have different sub
        # values for different deployments.
        value = anonymous_id_for_user(data['user'], None)
        return value


class PermissionsHandler(object):
    """ Permissions scope handler """

    def scope_permissions(self, _data):
        return ['administrator']

    def claim_administrator(self, data):
        """
        Return boolean indicating user's administrator status.

        For our purposes an administrator is any user with is_staff set to True.
        """
        return data['user'].is_staff


class ProfileHandler(object):
    """ Basic OpenID Connect `profile` scope handler with `locale` claim. """

    def scope_profile(self, _data):
        """ Add specialized claims. """
        return ['name', 'locale']

    def claim_name(self, data):
        """ User displayable full name. """
        user = data['user']
        profile = UserProfile.objects.get(user=user)
        return profile.name

    def claim_locale(self, data):
        """
        Return the locale for the users based on their preferences.
        Does not return a value if the users have not set their locale preferences.
        """

        # Calling UserPreference directly because it is not clear which user made the request.
        language = UserPreference.get_value(data['user'], LANGUAGE_KEY)

        # If the user has no language specified, return the default one.
        if not language:
            language = settings.LANGUAGE_CODE

        return language


class CourseAccessHandler(object):
    """
    Defines two new scopes: `course_instructor` and `course_staff`. Each one is
    valid only if the user is instructor or staff of at least one course.

    Each new scope has a corresponding claim: `instructor_courses` and
    `staff_courses` that lists the course_ids for which the user has instructor
    or staff privileges.

    The claims support claim request values: if there is no claim request, the
    value of the claim is the list all the courses for which the user has the
    corresponding privileges. If a claim request is used, then the value of the
    claim the list of courses from the requested values that have the
    corresponding privileges.

    For example, if the user is staff of course_a and course_b but not
    course_c, the claim corresponding to the scope request:

        scope = openid course_staff

    has the value:

        {staff_courses: [course_a, course_b] }

    For the claim request:

        claims = {userinfo: {staff_courses: {values=[course_b, course_d]}}}

    the corresponding claim will have the value:

        {staff_courses: [course_b] }.

    This is useful to quickly determine if a user has the right privileges for a
    given course.

    For a description of the function naming and arguments, see:

        `oauth2_provider/oidc/handlers.py`

    """

    COURSE_CACHE_TIMEOUT = getattr(settings, 'OIDC_COURSE_HANDLER_CACHE_TIMEOUT', 60)  # In seconds.

    def __init__(self, *_args, **_kwargs):
        self._course_cache = {}

    def scope_course_instructor(self, data):
        """
        Scope `course_instructor` valid only if the user is an instructor
        of at least one course.

        """

        # TODO: unfortunately there is not a faster and still correct way to
        # check if a user is instructor of at least one course other than
        # checking the access type against all known courses.
        course_ids = self.find_courses(data['user'], CourseInstructorRole.ROLE)
        return ['instructor_courses'] if course_ids else None

    def scope_course_staff(self, data):
        """
        Scope `course_staff` valid only if the user is an instructor of at
        least one course.

        """
        # TODO: see :method:CourseAccessHandler.scope_course_instructor
        course_ids = self.find_courses(data['user'], CourseStaffRole.ROLE)

        return ['staff_courses'] if course_ids else None

    def claim_instructor_courses(self, data):
        """
        Claim `instructor_courses` with list of course_ids for which the
        user has instructor privileges.

        """

        return self.find_courses(data['user'], CourseInstructorRole.ROLE, data.get('values'))

    def claim_staff_courses(self, data):
        """
        Claim `staff_courses` with list of course_ids for which the user
        has staff privileges.

        """

        return self.find_courses(data['user'], CourseStaffRole.ROLE, data.get('values'))

    def find_courses(self, user, access_type, values=None):
        """
        Find all courses for which the user has the specified access type. If
        `values` is specified, check only the courses from `values`.

        """

        # Check the instance cache and update if not present.  The instance
        # cache is useful since there are multiple scope and claims calls in the
        # same request.

        key = (user.id, access_type)
        if key in self._course_cache:
            course_ids = self._course_cache[key]
        else:
            course_ids = self._get_courses_with_access_type(user, access_type)
            self._course_cache[key] = course_ids

        # If values was specified, filter out other courses.
        if values is not None:
            course_ids = list(set(course_ids) & set(values))

        return course_ids

    # pylint: disable=missing-docstring
    def _get_courses_with_access_type(self, user, access_type):
        # Check the application cache and update if not present. The application
        # cache is useful since there are calls to different endpoints in close
        # succession, for example the id_token and user_info endpoints.

        key = '-'.join([str(self.__class__), str(user.id), access_type])
        course_ids = cache.get(key)

        if not course_ids:
            course_keys = CourseOverview.get_all_course_keys()

            # Global staff have access to all courses. Filter courses for non-global staff.
            if not GlobalStaff().has_user(user):
                course_keys = [course_key for course_key in course_keys if has_access(user, access_type, course_key)]

            course_ids = [unicode(course_key) for course_key in course_keys]

            cache.set(key, course_ids, self.COURSE_CACHE_TIMEOUT)

        return course_ids


class IDTokenHandler(OpenIDHandler, ProfileHandler, CourseAccessHandler, PermissionsHandler):
    """ Configure the ID Token handler for the LMS. """

    def claim_instructor_courses(self, data):
        # Don't return list of courses unless they are requested as essential.
        if data.get('essential'):
            return super(IDTokenHandler, self).claim_instructor_courses(data)
        else:
            return None

    def claim_staff_courses(self, data):
        # Don't return list of courses unless they are requested as essential.
        if data.get('essential'):
            return super(IDTokenHandler, self).claim_staff_courses(data)
        else:
            return None


class UserInfoHandler(OpenIDHandler, ProfileHandler, CourseAccessHandler, PermissionsHandler):
    """ Configure the UserInfo handler for the LMS. """
    pass
