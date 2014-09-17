""" Handlers for OpenID Connect provider. """

import branding
from courseware.access import has_access
from student.models import anonymous_id_for_user
from user_api.models import UserPreference
from lang_pref import LANGUAGE_KEY


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


class ProfileHandler(object):
    """ Basic OpenID Connect `profile` scope handler with `locale` claim. """

    def scope_profile(self, _data):
        """ Add the locale claim. """
        return ['locale']

    def claim_locale(self, data):
        """
        Return the locale for the users based on their preferences.
        Does not return a value if the users have not set their locale preferences.

        """

        language = UserPreference.get_preference(data['user'], LANGUAGE_KEY)
        return language


class CourseAccessHandler(object):
    """
    Defines two new scopes: `course_instructor` and `course_staff`. Each one is
    valid only if the user is instructor or staff of at least one course.

    Each new scope has a corresponding claim: `instructor_courses` and
    `staff_courses` that lists the course_ids for which the user as instructor
    or staff privileges.

    The claims support claim request values. In other words, if no claim is
    requested it returns all the courses for the corresponding privileges. If a
    claim request is used, then it only returns the from the list of requested
    values that have the corresponding privileges.

    For example, if the user is staff of course_a and course_b but not
    course_c, the request:

        scope = openid course_staff

    will return:

        {staff_courses: [course_a, course_b] }

    If the request is:

        claims = {userinfo: {staff_courses=[course_b, course_d]}}

    the result will be:

        {staff_courses: [course_b] }.

    This is useful to quickly determine if a user has the right
    privileges for a given course.

    For a description of the function naming and arguments, see:

        `oauth2_provider/oidc/handlers.py`

    """

    def scope_course_instructor(self, data):
        """
        Scope `course_instructor` valid only if the user is an instructor
        of at least one course.

        """

        course_ids = self._courses_with_access_type(data, 'instructor')
        return ['instructor_courses'] if course_ids else None

    def scope_course_staff(self, data):
        """
        Scope `course_staff` valid only if the user is an instructor of at
        least one course.

        """

        course_ids = self._courses_with_access_type(data, 'staff')
        return ['staff_courses'] if course_ids else None

    def claim_instructor_courses(self, data):
        """
        Claim `instructor_courses` with list of course_ids for which the
        user has instructor privileges.

        """
        return self._courses_with_access_type(data, 'instructor')

    def claim_staff_courses(self, data):
        """
        Claim `staff_courses` with list of course_ids for which the user
        has staff privileges.

        """
        return self._courses_with_access_type(data, 'staff')

    def _courses_with_access_type(self, data, access_type):
        """
        Utility function to list all courses for a user according to the
        access type.

        The field `data` follows the handler specification in:

            `oauth2_provider/oidc/handlers.py`

        """

        user = data['user']
        values = set(data.get('values', []))

        courses = branding.get_visible_courses()
        courses = (c for c in courses if has_access(user, access_type, c))
        course_ids = (unicode(c.id) for c in courses)

        # If values was provided, return only the requested authorized courses
        if values:
            return [c for c in course_ids if c in values]
        else:
            return [c for c in course_ids]


class IDTokenHandler(OpenIDHandler, ProfileHandler, CourseAccessHandler):
    """
    Configure the ID Token handler for the LMS.

    Note that the values of the claims `instructor_courses` and
    `staff_courses` are not included in the ID Token. The rationale is
    that for global staff, the list of courses returned could be very
    large. Instead they could check for specific courses using the
    UserInfo endpoint.

    """

    def claim_instructor_courses(self, data):
        # Don't return list of courses in ID Tokens
        return None

    def claim_staff_courses(self, data):
        # Don't return list of courses in ID Tokens
        return None


class UserInfoHandler(OpenIDHandler, ProfileHandler, CourseAccessHandler):
    """ Configure the UserInfo handler for the LMS. """
    pass
