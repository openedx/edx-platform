import logging
from openedx.core.djangoapps.enrollments.serializers import  LiveClassesSerializer , UserListSerializer ,CourseEnrollmentSerializer ,LiveClassEnrollmentSerializer ,LiveClassUserDetailsSerializer ,UserLiveClassDetailsSerializer, CourseEnrolledUserDetailsSerializer ,LoginStaffCourseDetailsSerializer
from common.djangoapps.student.models import LiveClassEnrollment
from openedx.core.djangoapps.enrollments import api
from openedx.core.lib.log_utils import audit_log
from openedx.core.djangoapps.enrollments.views import ApiKeyPermissionMixIn
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.split_modulestore_django.models import SplitModulestoreCourseIndex


from lms.djangoapps.course_api.serializers import CourseSerializer
from lms.djangoapps.course_api.forms import  CourseListGetForm
from lms.djangoapps.course_api.api import  list_courses ,course_detail, list_course_keys, _filter_by_search

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes

from openedx.core.djangoapps.course_groups.cohorts import CourseUserGroup, add_user_to_cohort, get_cohort_by_name
from common.djangoapps.student.roles import CourseStaffRole, GlobalStaff
from common.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.embargo import api as embargo_api
from openedx.core.djangoapps.enrollments.errors import (
    CourseEnrollmentError,
    CourseEnrollmentExistsError,
    CourseModeNotFoundError
)

from openedx.features.enterprise_support.api import (
    ConsentApiServiceClient,
    EnterpriseApiException,
    EnterpriseApiServiceClient,
    enterprise_enabled
)

from django.core.exceptions import (  # lint-amnesty, pylint: disable=wrong-import-order
    ObjectDoesNotExist,
    ValidationError
)
from openedx.core.djangoapps.user_api.preferences.api import update_email_opt_in
from openedx.core.lib.exceptions import CourseNotFoundError
from opaque_keys.edx.keys import CourseKey  # lint-amnesty, pylint: disable=wrong-import-order








from rest_framework.generics import ListAPIView , ListCreateAPIView ,CreateAPIView , RetrieveDestroyAPIView ,RetrieveUpdateDestroyAPIView # lint-amnesty, pylint: disable=wrong-import-order

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview, LiveClasses 
from rest_framework import permissions, status  # lint-amnesty, pylint: disable=wrong-import-order
from rest_framework.response import Response  # lint-amnesty, pylint: disable=wrong-import-order
from edx_rest_framework_extensions.auth.jwt.authentication import \
    JwtAuthentication  # lint-amnesty, pylint: disable=wrong-import-order
from edx_rest_framework_extensions.auth.session.authentication import \
    SessionAuthenticationAllowInactiveUser  # lint-amnesty, pylint: disable=wrong-import-order


from opaque_keys import InvalidKeyError 
from django.contrib.auth.models import User 
















log = logging.getLogger(__name__)
REQUIRED_ATTRIBUTES = {
    "credit": ["credit:provider_id"],
}





class LiveClassesApiListView(DeveloperErrorViewMixin, ListCreateAPIView):
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = LiveClassesSerializer
    #pagination_class = LiveClassesSerializer
    lookup_field = "username"

    # def get_queryset(self):
    #     created_by_id = self.kwargs.get('username')

    #     return LiveClasses.objects.filter(created_by=created_by_id)


    def get_queryset(self):
        return LiveClasses.objects.filter(created_by=self.request.user)




        


    def post(self, request, *args, **kwargs):
        """Upload documents"""
        try:
            serializer = self.serializer_class(
                data=request.data, context={'user':self.request.user}
            )
            serializer.is_valid(raise_exception=True)
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LiveClassesDeleteUpdateApiView(DeveloperErrorViewMixin, RetrieveUpdateDestroyAPIView):
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = LiveClassesSerializer
    queryset = LiveClasses.objects.all()
    model = LiveClasses
    lookup_field = "id"

 
            
    def delete(self, request, *args, **kwargs):
        

        try:
            live_class_id = self.model.objects.get(id=self.kwargs.get('id'))
            live_class_id.delete()
            return Response("Deleted Successfully", status=status.HTTP_200_OK)
        except self.model.DoesNotExist:
            return Response("Invalied Id", status=status.HTTP_422_UNPROCESSABLE_ENTITY)


    def patch(self, request, *args, **kwargs):
        try:
            instance= self.get_object()
            serializer = self.serializer_class(
                data=request.data, instance= instance , context={'user': self.request.user}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response("Updated Successfully", status=status.HTTP_200_OK)
        except self.model.DoesNotExist:
            return Response("Invalied Id", status=status.HTTP_422_UNPROCESSABLE_ENTITY)




class UserDetailsListApiView(DeveloperErrorViewMixin, ListAPIView):

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = None
    serializer_class = UserListSerializer
    queryset = User.objects.all()


    # def get_queryset(self):
    #     is_active = self.kwargs.get('is_active')

    #     return User.objects.filter(is_active=is_active)



    def get_serializer_class(self):
        """Get Serializer"""
        if self.request.method == 'GET':
            return UserListSerializer




class EnrollLiveClassCreateView(DeveloperErrorViewMixin, CreateAPIView):
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    #throttle_classes = (EnrollmentUserThrottle,)
    serializer_class = LiveClassEnrollmentSerializer
    #queryset = LiveClassEnrollment.objects.all()

    #pagination_class = LiveClassesSerializer
    

    def post(self, request, *args, **kwargs):
        """Upload documents"""
        try:
            serializer = self.serializer_class(
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class EnrollLiveClassUserDetailsView(DeveloperErrorViewMixin, ListCreateAPIView):
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    #throttle_classes = (EnrollmentUserThrottle,)
    serializer_class = LiveClassUserDetailsSerializer
    # pagination_class = LiveClassesSerializer
    lookup_url_kwarg = 'live_class_id'


    # lookup_field = "username"

    def get_queryset(self):
    
        return LiveClassEnrollment.objects.filter(live_class_id=self.kwargs.get('live_class_id'))



class EnrollCourseUserDetailsView(DeveloperErrorViewMixin, ListAPIView):
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    #throttle_classes = (EnrollmentUserThrottle,)
    serializer_class = CourseEnrolledUserDetailsSerializer
    # pagination_class = LiveClassesSerializer
    lookup_url_kwarg = 'course_id'


    # lookup_field = "username"

    def get_queryset(self):
    
        return CourseEnrollment.objects.filter(course_id=self.kwargs.get('course_id'))






class EnrollLiveClassUserDeleteApiView(DeveloperErrorViewMixin, RetrieveUpdateDestroyAPIView):
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    #throttle_classes = (EnrollmentUserThrottle,)
    serializer_class = UserLiveClassDetailsSerializer
    queryset = LiveClassEnrollment.objects.all()
    model = LiveClassEnrollment
    lookup_field = "id"



    def delete(self, request, *args, **kwargs):
        

        try:
            enroll_live_class_id = self.model.objects.get(id=self.kwargs.get('id'))
            enroll_live_class_id.delete()
            return Response("Deleted Successfully", status=status.HTTP_200_OK)
        except self.model.DoesNotExist:
            return Response("Invalied Id", status=status.HTTP_422_UNPROCESSABLE_ENTITY)




class LoginStaffCourseDetailsList(DeveloperErrorViewMixin, ListAPIView):
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    pagination_class =None
    #throttle_classes = (EnrollmentUserThrottle,)
    serializer_class = LoginStaffCourseDetailsSerializer
    # queryset = SplitModulestoreCourseIndex.objects.all()
    lookup_field = "edited_by_id"


    # def get(self, request, *args, **kwargs):
    #     edited_by_id = self.model.objects.get(edited_by_id=self.kwargs.get('edited_by'))


    def get_queryset(self):
    
        return SplitModulestoreCourseIndex.objects.filter(edited_by_id=self.kwargs.get('edited_by_id'))





class UserCourseEnrollment(CreateAPIView , ApiKeyPermissionMixIn):
    """
        **Use Cases**

            * Get a list of all course enrollments for the currently signed in user.

            * Enroll the currently signed in user in a course.

              Currently a user can use this command only to enroll the
              user in the default course mode. If this is not
              supported for the course, the request fails and returns
              the available modes.

              This command can use a server-to-server call to enroll a user in
              other modes, such as "verified", "professional", or "credit". If
              the mode is not supported for the course, the request will fail
              and return the available modes.

              You can include other parameters as enrollment attributes for a
              specific course mode. For example, for credit mode, you can
              include the following parameters to specify the credit provider
              attribute.

              * namespace: credit
              * name: provider_id
              * value: institution_name

        **Example Requests**

            POST /api/enrollment/v1/enrollment {

                "mode": "credit",
                "course_details":{"course_id": "edX/DemoX/Demo_Course"},
                "enrollment_attributes":[{"namespace": "credit","name": "provider_id","value": "hogwarts",},]

            }

            **POST Parameters**

              A POST request can include the following parameters.

              * user: Optional. The username of the currently logged in user.
                You cannot use the command to enroll a different user.

              * mode: Optional. The course mode for the enrollment. Individual
                users cannot upgrade their enrollment mode from the default. Only
                server-to-server requests can enroll with other modes.

              * is_active: Optional. A Boolean value indicating whether the
                enrollment is active. Only server-to-server requests are
                allowed to deactivate an enrollment.

              * course details: A collection that includes the following
                information.

                  * course_id: The unique identifier for the course.

              * email_opt_in: Optional. A Boolean value that indicates whether
                the user wants to receive email from the organization that runs
                this course.

              * enrollment_attributes: A dictionary that contains the following
                values.

                  * namespace: Namespace of the attribute
                  * name: Name of the attribute
                  * value: Value of the attribute

              * is_active: Optional. A Boolean value that indicates whether the
                enrollment is active. Only server-to-server requests can
                deactivate an enrollment.

              * mode: Optional. The course mode for the enrollment. Individual
                users cannot upgrade their enrollment mode from the default. Only
                server-to-server requests can enroll with other modes.

              * user: Optional. The user ID of the currently logged in user. You
                cannot use the command to enroll a different user.

              * enterprise_course_consent: Optional. A Boolean value that
                indicates the consent status for an EnterpriseCourseEnrollment
                to be posted to the Enterprise service."""

    
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)



    def post(self, request):
        # pylint: disable=too-many-statements
        """Enrolls the currently logged-in user in a course.

        Server-to-server calls may deactivate or modify the mode of existing enrollments. All other requests
        go through `add_enrollment()`, which allows creation of new and reactivation of old enrollments.
        """
        # Get the User, Course ID, and Mode from the request.

        username = request.data.get('user', request.user.username)
        course_id = request.data.get('course_details', {}).get('course_id')

        if not course_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Course ID must be specified to create a new enrollment."}
            )

        try:
            course_id = CourseKey.from_string(course_id)
        except InvalidKeyError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": f"No course '{course_id}' found for enrollment"
                }
            )

        mode = request.data.get('mode')

        has_api_key_permissions = self.has_api_key_permissions(request)

        # Check that the user specified is either the same user, or this is a server-to-server request.
        if not username:
            username = request.user.username
        if username != request.user.username and not has_api_key_permissions \
                and not GlobalStaff().has_user(request.user):
            # Return a 404 instead of a 403 (Unauthorized). If one user is looking up
            # other users, do not let them deduce the existence of an enrollment.
            return Response(status=status.HTTP_404_NOT_FOUND)

        if mode not in (CourseMode.AUDIT, CourseMode.HONOR, None) and not has_api_key_permissions \
                and not GlobalStaff().has_user(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": "User does not have permission to create enrollment with mode [{mode}].".format(
                        mode=mode
                    )
                }
            )

        try:
            # Lookup the user, instead of using request.user, since request.user may not match the username POSTed.
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_406_NOT_ACCEPTABLE,
                data={
                    'message': f'The user {username} does not exist.'
                }
            )

        embargo_response = embargo_api.get_embargo_response(request, course_id, user)

        if embargo_response:
            return embargo_response

        try:
            is_active = request.data.get('is_active')
            # Check if the requested activation status is None or a Boolean
            if is_active is not None and not isinstance(is_active, bool):
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        'message': ("'{value}' is an invalid enrollment activation status.").format(value=is_active)
                    }
                )

            explicit_linked_enterprise = request.data.get('linked_enterprise_customer')
            if explicit_linked_enterprise and has_api_key_permissions and enterprise_enabled():
                enterprise_api_client = EnterpriseApiServiceClient()
                consent_client = ConsentApiServiceClient()
                try:
                    enterprise_api_client.post_enterprise_course_enrollment(username, str(course_id))
                except EnterpriseApiException as error:
                    log.exception("An unexpected error occurred while creating the new EnterpriseCourseEnrollment "
                                  "for user [%s] in course run [%s]", username, course_id)
                    raise CourseEnrollmentError(str(error))  # lint-amnesty, pylint: disable=raise-missing-from
                kwargs = {
                    'username': username,
                    'course_id': str(course_id),
                    'enterprise_customer_uuid': explicit_linked_enterprise,
                }
                consent_client.provide_consent(**kwargs)

            enrollment_attributes = request.data.get('enrollment_attributes')
            enrollment = api.get_enrollment(username, str(course_id))
            mode_changed = enrollment and mode is not None and enrollment['mode'] != mode
            active_changed = enrollment and is_active is not None and enrollment['is_active'] != is_active
            missing_attrs = []
            if enrollment_attributes:
                actual_attrs = [
                    "{namespace}:{name}".format(**attr)
                    for attr in enrollment_attributes
                ]
                missing_attrs = set(REQUIRED_ATTRIBUTES.get(mode, [])) - set(actual_attrs)
            if (GlobalStaff().has_user(request.user) or has_api_key_permissions) and (mode_changed or active_changed):
                if mode_changed and active_changed and not is_active:
                    # if the requester wanted to deactivate but specified the wrong mode, fail
                    # the request (on the assumption that the requester had outdated information
                    # about the currently active enrollment).
                    msg = "Enrollment mode mismatch: active mode={}, requested mode={}. Won't deactivate.".format(
                        enrollment["mode"], mode
                    )
                    log.warning(msg)
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": msg})

                if missing_attrs:
                    msg = "Missing enrollment attributes: requested mode={} required attributes={}".format(
                        mode, REQUIRED_ATTRIBUTES.get(mode)
                    )
                    log.warning(msg)
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": msg})

                response = api.update_enrollment(
                    username,
                    str(course_id),
                    mode=mode,
                    is_active=is_active,
                    enrollment_attributes=enrollment_attributes,
                    # If we are updating enrollment by authorized api caller, we should allow expired modes
                    include_expired=has_api_key_permissions
                )
            else:
                # Will reactivate inactive enrollments.
                response = api.add_enrollment(
                    username,
                    str(course_id),
                    mode=mode,
                    is_active=is_active,
                    enrollment_attributes=enrollment_attributes,
                    enterprise_uuid=request.data.get('enterprise_uuid')
                )

            cohort_name = request.data.get('cohort')
            if cohort_name is not None:
                cohort = get_cohort_by_name(course_id, cohort_name)
                try:
                    add_user_to_cohort(cohort, user)
                except ValueError:
                    # user already in cohort, probably because they were un-enrolled and re-enrolled
                    log.exception('Cohort re-addition')
            email_opt_in = request.data.get('email_opt_in', None)
            if email_opt_in is not None:
                org = course_id.org
                update_email_opt_in(request.user, org, email_opt_in)

            log.info('The user [%s] has already been enrolled in course run [%s].', username, course_id)
            return Response(response)
        except CourseModeNotFoundError as error:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        "The [{mode}] course mode is expired or otherwise unavailable for course run [{course_id}]."
                    ).format(mode=mode, course_id=course_id),
                    "course_details": error.data
                })
        except CourseNotFoundError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": f"No course '{course_id}' found for enrollment"
                }
            )
        except CourseEnrollmentExistsError as error:
            log.warning('An enrollment already exists for user [%s] in course run [%s].', username, course_id)
            return Response(data=error.enrollment)
        except CourseEnrollmentError:
            log.exception("An error occurred while creating the new course enrollment for user "
                          "[%s] in course run [%s]", username, course_id)
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        "An error occurred while creating the new course enrollment for user "
                        "'{username}' in course '{course_id}'"
                    ).format(username=username, course_id=course_id)
                }
            )
        except CourseUserGroup.DoesNotExist:
            log.exception('Missing cohort [%s] in course run [%s]', cohort_name, course_id)
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": "An error occured while adding to cohort [%s]" % cohort_name
                })
        finally:
            # Assumes that the ecommerce service uses an API key to authenticate.
            if has_api_key_permissions:
                current_enrollment = api.get_enrollment(username, str(course_id))
                audit_log(
                    'enrollment_change_requested',
                    course_id=str(course_id),
                    requested_mode=mode,
                    actual_mode=current_enrollment['mode'] if current_enrollment else None,
                    requested_activation=is_active,
                    actual_activation=current_enrollment['is_active'] if current_enrollment else None,
                    user_id=user.id
                )


class UserCourseUnEnrollment(DeveloperErrorViewMixin, RetrieveUpdateDestroyAPIView):
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    #throttle_classes = (EnrollmentUserThrottle,)
    serializer_class = CourseEnrollmentSerializer
    queryset = CourseEnrollment.objects.all()
    model = CourseEnrollment
    lookup_field = "id"



    def delete(self, request, *args, **kwargs):
        

        try:
            enroll_course_id = self.model.objects.get(id=self.kwargs.get('id'))
            enroll_course_id.delete()
            return Response("Deleted Successfully", status=status.HTTP_200_OK)
        except self.model.DoesNotExist:
            return Response("Invalied Id", status=status.HTTP_422_UNPROCESSABLE_ENTITY)




@view_auth_classes(is_authenticated=False)
class CourseListView(DeveloperErrorViewMixin, ListAPIView):
    """
    **Use Cases**

        Request information on all courses visible to the specified user.

    **Example Requests**

        GET /api/courses/v1/courses/

    **Response Values**

        Body comprises a list of objects as returned by `CourseDetailView`.

    **Parameters**

        search_term (optional):
            Search term to filter courses (used by ElasticSearch).

        username (optional):
            The username of the specified user whose visible courses we
            want to see. The username is not required only if the API is
            requested by an Anonymous user.

        org (optional):
            If specified, visible `CourseOverview` objects are filtered
            such that only those belonging to the organization with the
            provided org code (e.g., "HarvardX") are returned.
            Case-insensitive.

        permissions (optional):
            If specified, it filters visible `CourseOverview` objects by
            checking if each permission specified is granted for the username.
            Notice that Staff users are always granted permission to list any
            course.

    **Returns**

        * 200 on success, with a list of course discovery objects as returned
          by `CourseDetailView`.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the specified user does not exist, or the requesting user does
          not have permission to view their courses.

        Example response:

            [
              {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                  "course_image": {
                    "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                    "name": "Course Image"
                  }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp"
              }
            ]
    """

    pagination_class = None
    serializer_class = CourseSerializer

    

    def get_queryset(self):
        """
        Yield courses visible to the user.
        """
        form = CourseListGetForm(self.request.query_params, initial={'requesting_user': self.request.user})
        if not form.is_valid():
        
            raise ValidationError(form.errors)
        return list_courses(
            self.request,
            form.cleaned_data['username'],
            org=form.cleaned_data['org'],
            filter_=form.cleaned_data['filter_'],
            search_term=form.cleaned_data['search_term'],
            permissions=form.cleaned_data['permissions']
            
        )


    # queryset = CourseOverview.objects.all()
    # def get_serializer_class(self):
    #     """Get Serializer"""
    #     if self.request.method == 'GET':
    #         return CourseSerializer                