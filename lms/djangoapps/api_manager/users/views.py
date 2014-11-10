""" API implementation for user-oriented interactions. """

import logging
from requests.exceptions import ConnectionError

from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Count, Q
from django.core.validators import validate_email, validate_slug, ValidationError
from django.conf import settings
from django.http import Http404
from django.utils.translation import get_language, ugettext_lazy as _
from rest_framework import status
from rest_framework import filters
from rest_framework.response import Response

from courseware import grades, module_render
from courseware.model_data import FieldDataCache
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
from openedx.core.djangoapps.course_groups.cohorts import (
    get_cohort_by_name,
    add_cohort,
    add_user_to_cohort,
    remove_user_from_cohort
)
from django_comment_common.models import Role, FORUM_ROLE_MODERATOR
from gradebook.models import StudentGradebook
from instructor.access import revoke_access, update_forum_role
from lang_pref import LANGUAGE_KEY
from notification_prefs.views import enable_notifications
from lms.lib.comment_client.user import User as CommentUser
from lms.lib.comment_client.utils import CommentClientRequestError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.models import CourseEnrollment, PasswordHistory, UserProfile
from openedx.core.djangoapps.user_api.models import UserPreference
from student.roles import CourseAccessRole, CourseInstructorRole, CourseObserverRole, CourseStaffRole, CourseAssistantRole, UserBasedRole
from util.bad_request_rate_limiter import BadRequestRateLimiter
from util.password_policy_validators import (
    validate_password_length, validate_password_complexity,
    validate_password_dictionary
)

from progress.serializers import CourseModuleCompletionSerializer
from api_manager.courseware_access import get_course, get_course_child, get_course_key, course_exists
from api_manager.permissions import SecureAPIView, SecureListAPIView, IdsInFilterBackend, HasOrgsFilterBackend
from api_manager.models import GroupProfile, APIUser as User
from organizations.serializers import OrganizationSerializer
from api_manager.utils import generate_base_uri, dict_has_items, extract_data_params
from projects.serializers import BasicWorkgroupSerializer
from .serializers import UserSerializer, UserCountByCitySerializer, UserRolesSerializer

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey, CourseKey
from opaque_keys.edx.locations import Location
from xmodule.modulestore import InvalidLocationError

from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)
AUDIT_LOG = logging.getLogger("audit")


def _serialize_user_profile(response_data, user_profile):
    """This function serialize user profile """
    response_data['title'] = user_profile.title
    response_data['full_name'] = user_profile.name
    response_data['city'] = user_profile.city
    response_data['country'] = user_profile.country.code
    response_data['level_of_education'] = user_profile.level_of_education
    response_data['year_of_birth'] = user_profile.year_of_birth
    response_data['gender'] = user_profile.gender
    response_data['avatar_url'] = user_profile.avatar_url

    return response_data


def _serialize_user(response_data, user):
    """
    Loads the object data into the response dict
    This should probably evolve to use DRF serializers
    """
    response_data['email'] = user.email
    response_data['username'] = user.username
    response_data['first_name'] = user.first_name
    response_data['last_name'] = user.last_name
    response_data['id'] = user.id
    response_data['is_active'] = user.is_active
    response_data['created'] = user.date_joined
    return response_data


def _save_content_position(request, user, course_key, position):
    """
    Records the indicated position for the specified course
    Really no reason to generalize this out of user_courses_detail aside from pylint complaining
    """
    parent_content_id = position['parent_content_id']
    child_content_id = position['child_content_id']
    if unicode(course_key) == parent_content_id:
        parent_descriptor, parent_key, parent_content = get_course(request, user, parent_content_id, load_content=True)  # pylint: disable=W0612
    else:
        parent_descriptor, parent_key, parent_content = get_course_child(request, user, course_key, parent_content_id, load_content=True)  # pylint: disable=W0612
    if not parent_descriptor:
        return None

    # no need to fetch the actual child descriptor (avoid round trip to Mongo database), we just need
    # the id
    child_key = None
    try:
        child_key = UsageKey.from_string(child_content_id)
    except InvalidKeyError:
        try:
            child_key = Location.from_deprecated_string(child_content_id)
        except (InvalidLocationError, InvalidKeyError):
            pass
    if not child_key:
        return None

    # call an optimized version
    _save_child_position(parent_content, child_key)

    return child_content_id


def _save_child_position(parent_descriptor, target_child_location):
    """
    Faster version than what is in the LMS since we don't need to load/traverse children descriptors,
    we just compare id's from the array of children
    """
    for position, child_location in enumerate(parent_descriptor.children, start=1):
        if child_location == target_child_location:
            # Only save if position changed
            if position != parent_descriptor.position:
                parent_descriptor.position = position
                parent_descriptor.save()


def _manage_role(course_descriptor, user, role, action):
    """
    Helper method for managing course/forum roles
    """
    supported_roles = ('instructor', 'staff', 'observer', 'assistant')
    forum_moderator_roles = ('instructor', 'staff', 'assistant')
    if role not in supported_roles:
        raise ValueError
    if action is 'allow':
        existing_role = CourseAccessRole.objects.filter(user=user, role=role, course_id=course_descriptor.id, org=course_descriptor.org)
        if not existing_role:
            new_role = CourseAccessRole(user=user, role=role, course_id=course_descriptor.id, org=course_descriptor.org)
            new_role.save()
        if role in forum_moderator_roles:
            try:
                dep_string = course_descriptor.id.to_deprecated_string()
                ssck = SlashSeparatedCourseKey.from_deprecated_string(dep_string)
                update_forum_role(ssck, user, FORUM_ROLE_MODERATOR, 'allow')
            except Role.DoesNotExist:
                try:
                    update_forum_role(course_descriptor.id, user, FORUM_ROLE_MODERATOR, 'allow')
                except Role.DoesNotExist:
                    pass

    elif action is 'revoke':
        revoke_access(course_descriptor, user, role)
        if role in forum_moderator_roles:
            # There's a possibilty that the user may play more than one role in a course
            # And that more than one of these roles allow for forum moderation
            # So we need to confirm the removed role was the only role for this user for this course
            # Before we can safely remove the corresponding forum moderator role
            user_instructor_courses = UserBasedRole(user, CourseInstructorRole.ROLE).courses_with_role()
            user_staff_courses = UserBasedRole(user, CourseStaffRole.ROLE).courses_with_role()
            user_assistant_courses = UserBasedRole(user, CourseAssistantRole.ROLE).courses_with_role()
            queryset = user_instructor_courses | user_staff_courses | user_assistant_courses
            queryset = queryset.filter(course_id=course_descriptor.id)
            if len(queryset) == 0:
                try:
                    dep_string = course_descriptor.id.to_deprecated_string()
                    ssck = SlashSeparatedCourseKey.from_deprecated_string(dep_string)
                    update_forum_role(ssck, user, FORUM_ROLE_MODERATOR, 'revoke')
                except Role.DoesNotExist:
                    try:
                        update_forum_role(course_descriptor.id, user, FORUM_ROLE_MODERATOR, 'revoke')
                    except Role.DoesNotExist:
                        pass


class UsersList(SecureListAPIView):
    """
    ### The UsersList view allows clients to retrieve/append a list of User entities
    - URI: ```/api/users/```
    - GET: Provides paginated list of users, it supports email, username, has_organizations and id filters
        Possible use cases
        GET /api/users?ids=23
        GET /api/users?ids=11,12,13&page=2
        GET /api/users?email={john@example.com}
        GET /api/users?username={john}
            * email: string, filters user set by email address
            * username: string, filters user set by username
        GET /api/users?has_organizations={true}
            * has_organizations: boolean, filters user set with organization association
        GET /api/users?has_organizations={false}
            * has_organizations: boolean, filters user set with no organization association

        Example JSON output {'count': '25', 'next': 'https://testserver/api/users?page=2', num_pages='3',
        'previous': None, 'results':[]}
        'next' and 'previous' keys would have value of None if there are not next or previous page after current page.

    - POST: Provides the ability to append to the User entity set
        * email: __required__, The unique email address for the User being created
        * username: __required__, The unique username for the User being created
        * password: __required__, String which matches enabled formatting constraints
        * title
        * first_name
        * last_name
        * is_active, Boolean flag controlling the User's account activation status
        * is_staff, Boolean flag controlling the User's administrative access/permissions
        * city
        * country, Two-character country code
        * level_of_education
        * year_of_birth, Four-digit integer value
        * gender, Single-character value (M/F)
        * avatar_url, pointer to the avatar/image resource
    - POST Example:

            {
                "email" : "honor@edx.org",
                "username" : "honor",
                "password" : "edx!@#",
                "title" : "Software Engineer",
                "first_name" : "Honor",
                "last_name" : "Student",
                "is_active" : False,
                "is_staff" : False,
                "city" : "Boston",
                "country" : "US",
                "level_of_education" : "hs",
                "year_of_birth" : "1996",
                "gender" : "F",
                "avatar_url" : "http://example.com/avatar.png"
            }
    ### Use Cases/Notes:
    * Password formatting policies can be enabled through the "ENFORCE_PASSWORD_POLICY" feature flag
    * The first_name and last_name fields are additionally concatenated and stored in the 'name' field of UserProfile
    * Values for level_of_education can be found in the LEVEL_OF_EDUCATION_CHOICES enum, located in common/student/models.py
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.DjangoFilterBackend, IdsInFilterBackend, HasOrgsFilterBackend)
    filter_fields = ('email', 'username', )

    def get(self, request, *args, **kwargs):
        """
        GET /api/users?ids=11,12,13.....&page=2
        """
        email = request.QUERY_PARAMS.get('email', None)
        username = request.QUERY_PARAMS.get('username', None)
        ids = request.QUERY_PARAMS.get('ids', None)
        has_orgs = request.QUERY_PARAMS.get('has_organizations', None)
        if email or username or ids or has_orgs:
            return self.list(request, *args, **kwargs)
        else:
            return Response({'message': _('Unfiltered request is not allowed.')}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        POST /api/users/
        """
        response_data = {}
        base_uri = generate_base_uri(request)
        email = request.DATA['email']
        username = request.DATA['username']
        password = request.DATA['password']
        first_name = request.DATA.get('first_name', '')
        last_name = request.DATA.get('last_name', '')
        is_active = request.DATA.get('is_active', None)
        is_staff = request.DATA.get('is_staff', False)
        city = request.DATA.get('city', '')
        country = request.DATA.get('country', '')
        level_of_education = request.DATA.get('level_of_education', '')
        year_of_birth = request.DATA.get('year_of_birth', '')
        gender = request.DATA.get('gender', '')
        title = request.DATA.get('title', '')
        avatar_url = request.DATA.get('avatar_url', None)
        # enforce password complexity as an optional feature
        if settings.FEATURES.get('ENFORCE_PASSWORD_POLICY', False):
            try:
                validate_password_length(password)
                validate_password_complexity(password)
                validate_password_dictionary(password)
            except ValidationError, err:
                response_data['message'] = _('Password: ') + '; '.join(err.messages)
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_email(email)
        except ValidationError:
            response_data['message'] = _('Valid e-mail is required.')
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_slug(username)
        except ValidationError:
            response_data['message'] = _('Username should only consist of A-Z and 0-9, with no spaces.')
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        # Create the User, UserProfile, and UserPreference records
        try:
            user = User.objects.create(email=email, username=username, is_staff=is_staff)
        except IntegrityError:
            response_data['message'] = "User '%s' already exists" % (username)
            response_data['field_conflict'] = "username or email"
            return Response(response_data, status=status.HTTP_409_CONFLICT)

        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        if is_active is not None:
            user.is_active = is_active
        if is_staff is not None:
            user.is_staff = is_staff
        user.save()

        # Be sure to always create a UserProfile record when adding users
        # Bad things happen with the UserSerializer if one does not exist
        profile = UserProfile(user=user)
        profile.name = '{} {}'.format(first_name, last_name)
        profile.city = city
        profile.country = country
        profile.level_of_education = level_of_education
        profile.gender = gender
        profile.title = title
        profile.avatar_url = avatar_url

        try:
            profile.year_of_birth = int(year_of_birth)
        except ValueError:
            # If they give us garbage, just ignore it instead
            # of asking them to put an integer.
            profile.year_of_birth = None

        profile.save()

        UserPreference.set_preference(user, LANGUAGE_KEY, get_language())

        # add this account creation to password history
        # NOTE, this will be a NOP unless the feature has been turned on in configuration
        password_history_entry = PasswordHistory()
        password_history_entry.create(user)

        # add to audit log
        AUDIT_LOG.info(u"API::New account created with user-id - {0}".format(user.id))

        # CDODGE:  @TODO: We will have to extend this to look in the CourseEnrollmentAllowed table and
        # auto-enroll students when they create a new account. Also be sure to remove from
        # the CourseEnrollmentAllow table after the auto-registration has taken place
        response_data = _serialize_user(response_data, user)
        response_data['uri'] = '{}/{}'.format(base_uri, str(user.id))
        return Response(response_data, status=status.HTTP_201_CREATED)


class UsersDetail(SecureAPIView):
    """
    ### The UsersDetail view allows clients to interact with a specific User entity
    - URI: ```/api/users/{user_id}```
    - GET: Returns a JSON representation of the specified User entity
    - POST: Provides the ability to modify specific fields for this User entity
        * email: __required__, The unique email address for the User being created
        * username: __required__, The unique username for the User being created
        * password: __required__, String which matches enabled formatting constraints
        * title
        * first_name
        * last_name
        * is_active, Boolean flag controlling the User's account activation status
        * is_staff, Boolean flag controlling the User's administrative access/permissions
        * city
        * country, Two-character country code
        * level_of_education
        * year_of_birth, Four-digit integer value
        * gender, Single-character value (M/F)
        * avatar_url, pointer to the avatar/image resource
    - POST Example:

            {
                "email" : "honor@edx.org",
                "username" : "honor",
                "password" : "edx!@#",
                "title" : "Software Engineer",
                "first_name" : "Honor",
                "last_name" : "Student",
                "is_active" : False,
                "is_staff" : False,
                "city" : "Boston",
                "country" : "US",
                "level_of_education" : "hs",
                "year_of_birth" : "1996",
                "gender" : "F",
                "avatar_url" : "http://example.com/avatar.png"
            }
    ### Use Cases/Notes:
    * Use the UsersDetail view to obtain the current state for a specific User
    * For POSTs, you may include only those parameters you wish to modify, for example:
        ** Modifying the 'city' without changing the 'level_of_education' field
        ** New passwords will be subject to both format and history checks, if enabled
    * A GET response will additionally include a list of URIs to available sub-resources:
        ** Related Courses (/api/users/{user_id}/courses)
        ** Related Groups(/api/users/{user_id}/groups)
    """

    def get(self, request, user_id):
        """
        GET /api/users/{user_id}
        """
        response_data = {}
        base_uri = generate_base_uri(request)
        try:
            existing_user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

        _serialize_user(response_data, existing_user)
        response_data['uri'] = base_uri
        response_data['resources'] = []
        resource_uri = '{}/groups'.format(base_uri)
        response_data['resources'].append({'uri': resource_uri})
        resource_uri = '{}/courses'.format(base_uri)
        response_data['resources'].append({'uri': resource_uri})

        existing_user_profile = UserProfile.objects.get(user_id=user_id)
        if existing_user_profile:
            _serialize_user_profile(response_data, existing_user_profile)

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, user_id):
        """
        POST /api/users/{user_id}
        """
        response_data = {}
        response_data['uri'] = generate_base_uri(request)
        first_name = request.DATA.get('first_name')  # Used in multiple spots below
        last_name = request.DATA.get('last_name')  # Used in multiple spots below
        # Add some rate limiting here by re-using the RateLimitMixin as a helper class
        limiter = BadRequestRateLimiter()
        if limiter.is_rate_limit_exceeded(request):
            AUDIT_LOG.warning("API::Rate limit exceeded in password_reset")
            response_data['message'] = _('Rate limit exceeded in password_reset.')
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)
        try:
            existing_user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            limiter.tick_bad_request_counter(request)
            existing_user = None
        if existing_user is None:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        # Ok, valid User, now update the provided fields
        if first_name:
            existing_user.first_name = first_name
        if last_name:
            existing_user.last_name = last_name
        is_active = request.DATA.get('is_active')
        if is_active is not None:
            existing_user.is_active = is_active
            response_data['is_active'] = existing_user.is_active
        is_staff = request.DATA.get('is_staff')
        if is_staff is not None:
            existing_user.is_staff = is_staff
            response_data['is_staff'] = existing_user.is_staff
        existing_user.save()

        username = request.DATA.get('username', None)
        if username:
            try:
                validate_slug(username)
            except ValidationError:
                response_data['message'] = _('Username should only consist of A-Z and 0-9, with no spaces.')
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

            existing_username = User.objects.filter(username=username).filter(~Q(id=user_id))
            if existing_username:
                response_data['message'] = "User '%s' already exists" % (username)
                response_data['field_conflict'] = "username"
                return Response(response_data, status=status.HTTP_409_CONFLICT)

            existing_user.username = username
            response_data['username'] = existing_user.username
            existing_user.save()

        password = request.DATA.get('password')
        if password:
            old_password_hash = existing_user.password
            _serialize_user(response_data, existing_user)
            if settings.FEATURES.get('ENFORCE_PASSWORD_POLICY', False):
                try:
                    validate_password_length(password)
                    validate_password_complexity(password)
                    validate_password_dictionary(password)
                except ValidationError, err:
                    # bad user? tick the rate limiter counter
                    AUDIT_LOG.warning("API::Bad password in password_reset.")
                    response_data['message'] = _('Password: ') + '; '.join(err.messages)
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            # also, check the password reuse policy
            err_msg = None
            if not PasswordHistory.is_allowable_password_reuse(existing_user, password):
                if existing_user.is_staff:
                    num_distinct = settings.ADVANCED_SECURITY_CONFIG['MIN_DIFFERENT_STAFF_PASSWORDS_BEFORE_REUSE']
                else:
                    num_distinct = settings.ADVANCED_SECURITY_CONFIG['MIN_DIFFERENT_STUDENT_PASSWORDS_BEFORE_REUSE']
                err_msg = _(
                    "You are re-using a password that you have used recently. You must "
                    "have {0} distinct password(s) before reusing a previous password."
                ).format(num_distinct)  # pylint: disable=E1101
            # also, check to see if passwords are getting reset too frequent
            if PasswordHistory.is_password_reset_too_soon(existing_user):
                num_days = settings.ADVANCED_SECURITY_CONFIG['MIN_TIME_IN_DAYS_BETWEEN_ALLOWED_RESETS']
                err_msg = _(
                    "You are resetting passwords too frequently. Due to security policies, "
                    "{0} day(s) must elapse between password resets"
                ).format(num_days)  # pylint: disable=E1101

            if err_msg:
                # We have an password reset attempt which violates some security policy,
                status_code = status.HTTP_403_FORBIDDEN
                response_data['message'] = err_msg
                return Response(response_data, status=status_code)

            existing_user.is_active = True
            existing_user.set_password(password)
            existing_user.save()
            update_user_password_hash = existing_user.password

            if update_user_password_hash != old_password_hash:
                # add this account creation to password history
                # NOTE, this will be a NOP unless the feature has been turned on in configuration
                password_history_entry = PasswordHistory()
                password_history_entry.create(existing_user)

        # Also update the UserProfile record for this User
        existing_user_profile = UserProfile.objects.get(user_id=user_id)
        if existing_user_profile:
            if first_name and last_name:
                existing_user_profile.name = '{} {}'.format(first_name, last_name)
            city = request.DATA.get('city')
            if city:
                existing_user_profile.city = city
            country = request.DATA.get('country')
            if country:
                existing_user_profile.country = country
            level_of_education = request.DATA.get('level_of_education')
            if level_of_education:
                existing_user_profile.level_of_education = level_of_education
            year_of_birth = request.DATA.get('year_of_birth')
            try:
                year_of_birth = int(year_of_birth)
            except (ValueError, TypeError):
                # If they give us garbage, just ignore it instead
                # of asking them to put an integer.
                year_of_birth = None
            if year_of_birth:
                existing_user_profile.year_of_birth = year_of_birth
            gender = request.DATA.get('gender')
            if gender:
                existing_user_profile.gender = gender
            # Empty title is also allowed
            title = request.DATA.get('title', None)
            existing_user_profile.title = title
            avatar_url = request.DATA.get('avatar_url')
            if avatar_url:
                existing_user_profile.avatar_url = avatar_url

            existing_user_profile.save()
        return Response(response_data, status=status.HTTP_200_OK)


class UsersGroupsList(SecureAPIView):
    """
    ### The UsersGroupsList view allows clients to interact with the set of Group entities related to the specified User
    - URI: ```/api/users/{user_id}/groups/```
    - GET: Returns a JSON representation (array) of the set of related Group entities
        * type: Set filtering parameter
        * course: Set filtering parameter to groups associated to a course or courses
        - URI: ```/api/users/{user_id}/groups/?type=series,seriesX&course=slashes%3AMITx%2B999%2BTEST_COURSE```
        * xblock_id: filters group data and returns those groups where xblock_id matches given xblock_id
    - POST: Append a Group entity to the set of related Group entities for the specified User
        * group_id: __required__, The identifier for the Group being added
    - POST Example:

            {
                "group_id" : 123
            }
    ### Use Cases/Notes:
    * Use the UsersGroupsList view to manage Group membership for a specific User
    * For example, you could display a list of all of a User's groups in a dashboard or administrative view
    * Optionally include the 'type' parameter to retrieve a subset of groups with a matching 'group_type' value
    """

    def post(self, request, user_id):
        """
        POST /api/users/{user_id}/groups
        """
        response_data = {}
        group_id = request.DATA['group_id']
        base_uri = generate_base_uri(request)
        response_data['uri'] = '{}/{}'.format(base_uri, str(group_id))
        try:
            existing_user = User.objects.get(id=user_id)
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            existing_user.groups.get(id=existing_group.id)
            response_data['uri'] = '{}/{}'.format(base_uri, existing_group.id)
            response_data['message'] = "Relationship already exists."
            return Response(response_data, status=status.HTTP_409_CONFLICT)
        except ObjectDoesNotExist:
            existing_user.groups.add(existing_group.id)
            response_data['uri'] = '{}/{}'.format(base_uri, existing_group.id)
            response_data['group_id'] = str(existing_group.id)
            response_data['user_id'] = str(existing_user.id)
            return Response(response_data, status=status.HTTP_201_CREATED)

    def get(self, request, user_id):
        """
        GET /api/users/{user_id}/groups?type=workgroup
        """
        try:
            existing_user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        group_type = request.QUERY_PARAMS.get('type', None)
        course = request.QUERY_PARAMS.get('course', None)
        data_params = extract_data_params(request)
        response_data = {}
        base_uri = generate_base_uri(request)
        response_data['uri'] = base_uri
        groups = existing_user.groups.all()
        if group_type:
            group_type = group_type.split(',')
            groups = groups.filter(groupprofile__group_type__in=group_type)
        if course:
            course = course.split(',')
            groups = groups.filter(coursegrouprelationship__course_id__in=course)
        if data_params:
            groups = [group for group in groups if dict_has_items(group.groupprofile.data, data_params)]
        response_data['groups'] = []
        for group in groups:
            group_profile = GroupProfile.objects.get(group_id=group.id)
            group_data = {}
            group_data['id'] = group.id
            group_data['name'] = group_profile.name
            response_data['groups'].append(group_data)
        return Response(response_data, status=status.HTTP_200_OK)


class UsersGroupsDetail(SecureAPIView):
    """
    ### The UsersGroupsDetail view allows clients to interact with a specific User-Group relationship
    - URI: ```/api/users/{user_id}/groups/{group_id}```
    - GET: Returns a JSON representation of the specified User-Group relationship
    - DELETE: Removes an existing User-Group relationship
    ### Use Cases/Notes:
    * Use the UsersGroupsDetail to validate that a User is a member of a specific Group
    * Cancelling a User's membership in a Group is as simple as calling DELETE on the URI
    """

    def get(self, request, user_id, group_id):
        """
        GET /api/users/{user_id}/groups/{group_id}
        """
        response_data = {}
        try:
            existing_user = User.objects.get(id=user_id, is_active=True)
            existing_relationship = existing_user.groups.get(id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        response_data['user_id'] = existing_user.id
        response_data['group_id'] = existing_relationship.id
        response_data['uri'] = generate_base_uri(request)
        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, user_id, group_id):  # pylint: disable=W0612,W0613
        """
        DELETE /api/users/{user_id}/groups/{group_id}
        """
        existing_user = User.objects.get(id=user_id, is_active=True)
        existing_user.groups.remove(group_id)
        existing_user.save()
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class UsersCoursesList(SecureAPIView):
    """
    ### The UsersCoursesList view allows clients to interact with the set of Course entities related to the specified User
    - URI: ```/api/users/{user_id}/courses/```
    - GET: Returns a JSON representation (array) of the set of related Course entities
    - POST: Append a Group entity to the set of related Group entities for the specified User
        * course_id: __required__, The identifier (aka, location/key) for the Course being added
    - POST Example:

            {
                "course_id" : "edx/demo/course"
            }
    ### Use Cases/Notes:
    * POST to the UsersCoursesList view to create a new Course enrollment for the specified User (aka, Student)
    * Perform a GET to generate a list of all active Course enrollments for the specified User
    """

    def post(self, request, user_id):
        """
        POST /api/users/{user_id}/courses/
        """
        response_data = {}
        user_id = user_id
        course_id = request.DATA['course_id']
        try:
            user = User.objects.get(id=user_id)
            course_descriptor, course_key, course_content = get_course(request, user, course_id)  # pylint: disable=W0612
            if not course_descriptor:
                return Response({}, status=status.HTTP_404_NOT_FOUND)
        except (ObjectDoesNotExist, ValueError):
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        base_uri = generate_base_uri(request)
        course_enrollment = CourseEnrollment.enroll(user, course_key)
        # Ensure the user is in a cohort. Add it explicitly in the default_cohort
        try:
            default_cohort = get_cohort_by_name(course_key, CourseUserGroup.default_cohort_name)
        except CourseUserGroup.DoesNotExist:
            default_cohort = add_cohort(course_key, CourseUserGroup.default_cohort_name)
        add_user_to_cohort(default_cohort, user.username)
        log.debug('User "{}" has been automatically added in cohort "{}" for course "{}"'.format(
            user.username, default_cohort.name, course_descriptor.display_name)
        )
        response_data['uri'] = '{}/{}'.format(base_uri, course_key)
        response_data['id'] = unicode(course_key)
        response_data['name'] = course_descriptor.display_name
        response_data['is_active'] = course_enrollment.is_active
        return Response(response_data, status=status.HTTP_201_CREATED)

    def get(self, request, user_id):
        """
        GET /api/users/{user_id}/courses/
        """
        base_uri = generate_base_uri(request)
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        enrollments = CourseEnrollment.enrollments_for_user(user=user)
        response_data = []
        for enrollment in enrollments:
            course_descriptor, course_key, course_content = get_course(request, user, unicode(enrollment.course_id))  # pylint: disable=W0612
            # NOTE: It is possible that a course has been hard deleted from the courseware
            # database, but the enrollment row in the SQL database still exists
            if course_descriptor:
                course_data = {
                    "id": unicode(course_key),
                    "uri": '{}/{}'.format(base_uri, unicode(course_key)),
                    "is_active": enrollment.is_active,
                    "name": course_descriptor.display_name,
                    "start": getattr(course_descriptor, 'start', None),
                    "end": getattr(course_descriptor, 'end', None)
                }
                response_data.append(course_data)
            else:
                log.warning("User {0} enrolled in course_id {1}, but course could not be found.".format(user_id, unicode(enrollment.course_id)))

        return Response(response_data, status=status.HTTP_200_OK)


def _get_current_position_loc(parent_module):
    """
    An optimized lookup for the current position. The LMS version can cause unnecessary round trips to
    the Mongo database
    """
    if not hasattr(parent_module, 'position'):
        return None

    if not parent_module.children:
        return None

    index = 0
    if parent_module.position:
        index = parent_module.position - 1   # position is 1 indexed

    if 0 <= index < len(parent_module.children):
        return parent_module.children[index]

    return parent_module.children[0]


class UsersCoursesDetail(SecureAPIView):
    """
    ### The UsersCoursesDetail view allows clients to interact with a specific User-Course relationship (aka, enrollment)
    - URI: ```/api/users/{user_id}/courses/{course_id}```
    - POST: Stores the last-known location for the Course, for the specified User
        * position: The parent-child identifier set for the Content being set as the last-known position, consisting of:
        ** parent_content_id, normally the Course identifier
        ** child_content_id, normally the Chapter identifier
    - POST Example:

            {
                "position" : {
                    "parent_content_id" : "edX/Open_DemoX/edx_demo_course",
                    "child_content_id" : "i4x://edX/Open_DemoX/chapter/d8a6192ade314473a78242dfeedfbf5b"
                }
            }
    - GET: Returns a JSON representation of the specified User-Course relationship
    - DELETE: Inactivates (but does not remove) a Course relationship for the specified User
    ### Use Cases/Notes:
    * Use the UsersCoursesDetail view to manage EXISTING Course enrollments
    * Use GET to confirm that a User is actively enrolled in a particular course
    * Use DELETE to unenroll a User from a Course (inactivates the enrollment)
    * Use POST to record the last-known position within a Course (essentially, a bookmark)
    * Note: To create a new Course enrollment, see UsersCoursesList
    """

    def post(self, request, user_id, course_id):
        """
        POST /api/users/{user_id}/courses/{course_id}
        """
        base_uri = generate_base_uri(request)
        response_data = {}
        response_data['uri'] = base_uri
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        if not course_exists(request, user, course_id):
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        response_data['user_id'] = user.id
        response_data['course_id'] = course_id

        if request.DATA['positions']:
            course_key = get_course_key(course_id)
            response_data['positions'] = []
            for position in request.DATA['positions']:
                content_position = _save_content_position(
                    request,
                    user,
                    course_key,
                    position
                )
                if not content_position:
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                response_data['positions'].append(content_position)
        return Response(response_data, status=status.HTTP_200_OK)

    def get(self, request, user_id, course_id):
        """
        GET /api/users/{user_id}/courses/{course_id}
        """
        response_data = {}
        base_uri = generate_base_uri(request)
        try:
            user = User.objects.get(id=user_id, is_active=True)
            course_descriptor, course_key, course_content = get_course(request, user, course_id)
        except (ObjectDoesNotExist, ValueError):
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        if not CourseEnrollment.is_enrolled(user, course_key):
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        response_data['user_id'] = user.id
        response_data['course_id'] = course_id
        response_data['uri'] = base_uri
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course_key,
            user,
            course_descriptor,
            depth=0)
        course_module = module_render.get_module_for_descriptor(
            user,
            request,
            course_descriptor,
            field_data_cache,
            course_key)
        response_data['position'] = course_module.position
        response_data['position_tree'] = {}
        parent_module = course_module
        while parent_module is not None:

            current_child_loc = _get_current_position_loc(parent_module)

            if  current_child_loc:
                response_data['position_tree'][current_child_loc.category] = {}
                response_data['position_tree'][current_child_loc.category]['id'] = unicode(current_child_loc)

                _,_,parent_module = get_course_child(request, user, course_key, unicode(current_child_loc), load_content=True)

            else:
                parent_module = None
        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, user_id, course_id):
        """
        DELETE /api/users/{user_id}/courses/{course_id}
        """
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        if not course_exists(request, user, course_id):
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        course_key = get_course_key(course_id)
        try:
            cohort = CourseUserGroup.objects.get(
                course_id=course_key,
                users__id=user.id,
                group_type=CourseUserGroup.COHORT,
            )
            remove_user_from_cohort(cohort, user.username)
        except ObjectDoesNotExist:
            pass
        CourseEnrollment.unenroll(user, course_key)
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class UsersCoursesGradesDetail(SecureAPIView):
    """
    ### The UsersCoursesGradesDetail view allows clients to interact with the User's gradebook for a particular Course
    - URI: ```/api/users/{user_id}/courses/{course_id}/grades```
    - GET: Returns a JSON representation of the specified Course gradebook
    ### Use Cases/Notes:
    * Use the UsersCoursesDetail view to manage the User's gradebook for a Course enrollment
    * Use GET to retrieve the Course gradebook for the specified User
    """

    def get(self, request, user_id, course_id):
        """
        GET /api/users/{user_id}/courses/{course_id}/grades
        """

        # The pre-fetching of groups is done to make auth checks not require an
        # additional DB lookup (this kills the Progress page in particular).
        try:
            student = User.objects.prefetch_related("groups").get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        # @TODO: Add authorization check here once we get caller identity
        # Only student can get his/her own information *or* course staff
        # can get everyone's grades
        # get the full course tree with depth=None which reduces the number of
        # round trips to the database
        course_descriptor, course_key, course_content = get_course(request, student, course_id, depth=None)  # pylint: disable=W0612
        if not course_descriptor:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        progress_summary = grades.progress_summary(student, request, course_descriptor)  # pylint: disable=W0612
        grade_summary = grades.grade(student, request, course_descriptor)
        grading_policy = course_descriptor.grading_policy
        current_grade = 0
        proforma_grade = 0

        queryset = StudentGradebook.objects.filter(
            user=student,
            course_id__exact=course_key,
        )
        if len(queryset):
            current_grade = queryset[0].grade
            proforma_grade = grades.calculate_proforma_grade(grade_summary, grading_policy)

        response_data = {
            'courseware_summary': progress_summary,
            'grade_summary': grade_summary,
            'grading_policy': grading_policy,
            'current_grade': current_grade,
            'proforma_grade': proforma_grade
        }
        return Response(response_data)


class UsersPreferences(SecureAPIView):
    """
    ### The UsersPreferences view allows clients to interact with the set of Preference key-value pairs related to the specified User
    - URI: ```/api/users/{user_id}/preferences/```
    - GET: Returns a JSON representation (dict) of the set of User preferences
    - POST: Append a new UserPreference key-value pair to the set of preferences for the specified User
        * "keyname": __required__, The identifier (aka, key) for the UserPreference being added.  Values must be strings
    - POST Example:

            {
                "favorite_color" : "blue"
            }
    ### Use Cases/Notes:
    * POSTing a non-string preference value will result in a 400 Bad Request response from the server
    * POSTing a duplicate preference will cause the existing preference to be overwritten (effectively a PUT operation)
    """

    def get(self, request, user_id):  # pylint: disable=W0613
        """
        GET returns the preferences for the specified user
        """

        response_data = {}

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)

        for preference in user.preferences.all():
            response_data[preference.key] = preference.value

        return Response(response_data)

    def post(self, request, user_id):
        """
        POST adds a new entry into the UserPreference table
        """

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        if not len(request.DATA):
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        # do a quick inspection to make sure we're only getting strings as values
        for key in request.DATA.keys():
            value = request.DATA[key]
            if not isinstance(value, basestring):
                return Response({}, status=status.HTTP_400_BAD_REQUEST)

        status_code = status.HTTP_200_OK
        for key in request.DATA.keys():
            value = request.DATA[key]

            # see if the key already exists
            found = None
            for preference in user.preferences.all():
                if preference.key == key:
                    found = preference
                    break

            if found:
                found.value = value
                found.save()
            else:
                preference = UserPreference.objects.create(user_id=user_id, key=key, value=value)
                preference.save()
                status_code = status.HTTP_201_CREATED

        return Response({}, status_code)

class UsersPreferencesDetail(SecureAPIView):
    """
    ### The UsersPreferencesDetail view allows clients to interact with the User's preferences
    - URI: ```/api/users/{user_id}/preferences/{preference_id}```
    - DELETE: Removes the specified preference from the user's record
    ### Use Cases/Notes:
    * Use DELETE to remove the last-visited course for a user (for example)
    """

    def get(self, request, user_id, preference_id):  # pylint: disable=W0613
        """
        GET returns the specified preference for the specified user
        """
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        response_data = {}
        try:
            response_data[preference_id] = user.preferences.get(key=preference_id).value
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        return Response(response_data)

    def delete(self, request, user_id, preference_id):  # pylint: disable=W0613
        """
        DELETE /api/users/{user_id}/preferences/{preference_id}
        """
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        for preference in user.preferences.all():
            if preference.key == preference_id:
                UserPreference.objects.get(user_id=user_id, key=preference.key).delete()
                break
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class UsersOrganizationsList(SecureListAPIView):
    """
    ### The UserOrganizationsList view allows clients to retrieve a list of organizations a user
    belongs to
    - URI: ```/api/users/{user_id}/organizations/```
    - GET: Provides paginated list of organizations for a user
    """

    serializer_class = OrganizationSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            raise Http404

        return user.organizations.all()


class UsersWorkgroupsList(SecureListAPIView):
    """
    ### The UsersWorkgroupsList view allows clients to retrieve a list of workgroups a user
    belongs to
    - URI: ```/api/users/{user_id}/workgroups/```
    - GET: Provides paginated list of workgroups for a user
    To filter the user's workgroup set by course
    GET ```/api/users/{user_id}/workgroups/?course_id={course_id}```
    """

    serializer_class = BasicWorkgroupSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        course_id = self.request.QUERY_PARAMS.get('course_id', None)
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            raise Http404

        queryset = user.workgroups.all()

        if course_id:
            queryset = queryset.filter(project__course_id=course_id)
        return queryset


class UsersCoursesCompletionsList(SecureListAPIView):
    """
    ### The UsersCoursesCompletionsList view allows clients to retrieve a list of course completions
    for a user
    - URI: ```/api/users/{user_id}/courses/{course_id}/completions/```
    - GET: Provides paginated list of course completions a user
    To filter the user's course completions by course content
    GET ```/api/users/{user_id}/courses/{course_id}/completions/?content_id={content_id}```
    """

    serializer_class = CourseModuleCompletionSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        course_id = self.kwargs.get('course_id', None)
        content_id = self.request.QUERY_PARAMS.get('content_id', None)
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            raise Http404

        queryset = user.course_completions.all()

        if course_id:
            queryset = queryset.filter(course_id=course_id)
        if content_id:
            queryset = queryset.filter(content_id=content_id)

        return queryset


class UsersSocialMetrics(SecureListAPIView):
    """
    ### The UsersSocialMetrics view allows clients to query about the activity of a user in the
    forums
    - URI: ```/api/users/{user_id}/courses/{course_id}/metrics/social/```
    - GET: Returns a list of social metrics for that user in the specified course
    """

    def get(self, request, user_id, course_id):  # pylint: disable=W0613,W0221
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)

        comment_user = CommentUser.from_django_user(user)

        # be robust to the try of course_id we get from caller
        try:
            # assume new style
            course_key = CourseKey.from_string(course_id)
            slash_course_id = course_key.to_deprecated_string()
        except:
            # assume course_id passed in is legacy format
            slash_course_id = course_id

        comment_user.course_id = slash_course_id

        try:
            data = (comment_user.social_stats())[user_id]
            http_status = status.HTTP_200_OK
        except (CommentClientRequestError, ConnectionError), error:
            data = {
                "err_msg": str(error)
            }
            http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        return Response(data, http_status)


class UsersMetricsCitiesList(SecureListAPIView):
    """
    ### The UsersMetricsCitiesList view allows clients to retrieve ordered list of user
    count by city
    - URI: ```/api/users/metrics/cities/```
    - GET: Provides paginated list of user count
    To get user count a particular city filter can be applied
    GET ```/api/users/metrics/cities/?city={city}```
    """

    serializer_class = UserCountByCitySerializer

    def get_queryset(self):
        city = self.request.QUERY_PARAMS.get('city', None)
        queryset = User.objects.all()
        if city:
            queryset = queryset.filter(profile__city__iexact=city)

        queryset = queryset.values('profile__city').annotate(count=Count('profile__city'))\
            .filter(count__gt=0).order_by('-count')
        return queryset


class UsersRolesList(SecureListAPIView):
    """
    ### The UsersRolesList view allows clients to interact with the User's roleset
    - URI: ```/api/users/{user_id}/courses/{course_id}/roles```
    - GET: Returns a JSON representation of the specified Course roleset
    - POST: Adds a new role to the User's roleset
    - PUT: Replace the existing roleset with the provided roleset

    ### Use Cases/Notes:
    * Use the UsersRolesList view to manage a User's TA status
    * Use GET to retrieve the set of roles a User plays for a particular course
    * Use POST to grant a role to a particular User
    * Use PUT to perform a batch replacement of all roles assigned to a User
    """

    serializer_class = UserRolesSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            raise Http404

        instructor_courses = UserBasedRole(user, CourseInstructorRole.ROLE).courses_with_role()
        staff_courses = UserBasedRole(user, CourseStaffRole.ROLE).courses_with_role()
        observer_courses = UserBasedRole(user, CourseObserverRole.ROLE).courses_with_role()
        assistant_courses = UserBasedRole(user, CourseAssistantRole.ROLE).courses_with_role()
        queryset = instructor_courses | staff_courses | observer_courses | assistant_courses

        course_id = self.request.QUERY_PARAMS.get('course_id', None)
        if course_id:
            if not course_exists(self.request, user, course_id):
                raise Http404
            course_key = get_course_key(course_id)
            queryset = queryset.filter(course_id=course_key)

        role = self.request.QUERY_PARAMS.get('role', None)
        if role:
            queryset = queryset.filter(role=role)

        return queryset

    def post(self, request, user_id):
        """
        POST /api/users/{user_id}/roles/
        """
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            raise Http404

        course_id = request.DATA.get('course_id', None)
        course_descriptor, course_key, course_content = get_course(self.request, self.request.user, course_id)  # pylint: disable=W0612
        if not course_descriptor:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        role = request.DATA.get('role', None)
        try:
            _manage_role(course_descriptor, user, role, 'allow')
        except ValueError:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        return Response(request.DATA, status=status.HTTP_201_CREATED)

    def put(self, request, user_id):
        """
        PUT /api/users/{user_id}/roles/
        """
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            raise Http404

        if not len(request.DATA['roles']):
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        ignore_roles = request.DATA.get('ignore_roles', [])
        current_roles = self.get_queryset()
        for current_role in current_roles:
            if current_role.role not in ignore_roles:
                course_descriptor, course_key, course_content = get_course(request, user, unicode(current_role.course_id))  # pylint: disable=W0612
                _manage_role(course_descriptor, user, current_role.role, 'revoke')
        for role in request.DATA['roles']:
            if role['role'] not in ignore_roles:
                try:
                    course_id = role['course_id']
                    course_descriptor, course_key, course_content = get_course(request, user, course_id)  # pylint: disable=W0612
                    if not course_descriptor:
                        raise ValueError  # ValueError is also thrown by the following role setters
                    _manage_role(course_descriptor, user, role['role'], 'allow')
                except ValueError:
                    # Restore the current roleset to the User
                    for current_role in current_roles:
                        course_descriptor, course_key, course_content = get_course(
                            request, user, unicode(current_role.course_id))  # pylint: disable=W0612
                        _manage_role(course_descriptor, user, current_role.role, 'allow')
                    return Response({}, status=status.HTTP_400_BAD_REQUEST)
        return Response(request.DATA, status=status.HTTP_200_OK)


class UsersRolesCoursesDetail(SecureAPIView):
    """
    ### The UsersRolesCoursesDetail view allows clients to interact with a specific User/Course Role
    - URI: ```/api/users/{user_id}/roles/{role}/courses/{course_id}/```
    - DELETE: Removes an existing Course Role specification
    ### Use Cases/Notes:
    * Use the DELETE operation to revoke a particular role for the specified user
    """
    def delete(self, request, user_id, role, course_id):  # pylint: disable=W0613
        """
        DELETE /api/users/{user_id}/roles/{role}/courses/{course_id}
        """
        course_descriptor, course_key, course_content = get_course(self.request, self.request.user, course_id)  # pylint: disable=W0612
        if not course_descriptor:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        try:
            _manage_role(course_descriptor, user, role, 'revoke')
        except ValueError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        return Response({}, status=status.HTTP_204_NO_CONTENT)
