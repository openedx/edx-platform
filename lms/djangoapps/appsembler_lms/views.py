import logging
import unicodedata

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import caches, InvalidCacheBackendError
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from opaque_keys.edx.locator import CourseLocator
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from courseware.courses import get_course
from instructor.enrollment import enroll_email
from student.forms import AccountCreationForm
from student.views import _do_create_account
from .models import Organization
from .permissions import SecretKeyPermission
from .serializers import UserSignupSerializer



logger = logging.getLogger(__name__)
# TODO: put this into settings
APPSEMBLER_EMAIL = 'support@appsembler.com'


class UserSignupAPIView(GenericAPIView):
    permission_classes = (SecretKeyPermission,)
    serializer_class = UserSignupSerializer

    def post(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        if serializer.is_valid():
            try:
                user = self._create_user(serializer.data)
                response_data = {
                    'username': user.username,
                    'email': user.email
                }
                message_data = {}
                if serializer.data.get('course_id'):
                    course_name = self._enroll_in_course(user, serializer.data.get('course_id'))
                    response_data['course'] = message_data['course_name'] = course_name

                message_data.update(serializer.data)
                # TODO: extract appsembler info (phone/email) from email template
                subject = render_to_string('appsembler/emails/user_welcome_email_subject.txt')
                message = render_to_string('appsembler/emails/user_welcome_email.txt', message_data)
                send_mail(subject, message, 'info@appsembler.com', [user.email], fail_silently=False)
                return Response(status=status.HTTP_201_CREATED, data=response_data)
            except Exception as e:
                # TODO: check different exceptions and handle them
                pass
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def _create_user(self, data):
        try:
            user = User.objects.get(email=data.get('email'))
        except User.DoesNotExist:
            # filter out any spaces and punctuation
            username = u''.join(ch for ch in data.get('name') if ch.isalnum())
            username = unicodedata.normalize('NFKD', username).encode('ascii', 'ignore')

            # make sure username is unique
            i = 1
            while User.objects.filter(username=username):
                username = username + str(i)
                i += 1

            form = AccountCreationForm(
                data={
                    'username': username,
                    'email': data.get('email'),
                    'password': data.get('password'),
                    'name': data.get('name')
                },
                tos_required=False
            )
            try:
                (user, profile, registration) = _do_create_account(form)
            except ValidationError as e:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
            # create_comments_service_user(user)  # TODO: do we need this? if so, fix it

            # if the organization does not exist yet, create it
            try:
                organization = Organization.objects.get(key=data.get('org'))
            except Organization.DoesNotExist:
                organization = Organization(key=data.get('org'),
                                            display_name=data.get('org_name'))
                organization.save()

            # add the organization to the user
            profile.organization = organization
            profile.save()

            user.is_active = True
            user.save()
        return user

    def _enroll_in_course(self, user, course_id_str):
        try:
            course_id = CourseLocator.from_string(course_id_str)
            enrollment = enroll_email(
                course_id, user.email, auto_enroll=True, email_students=False
            )
            course = get_course(course_id)
            course_name = course.display_name
        # if we can't find the course, log as an error, since we know we sent a course id
        except ValueError:
            logger.error("Could not find this course: {0}".format(course_id_str))
            course_name = None
        return course_name


user_signup_endpoint = UserSignupAPIView.as_view()


@require_POST
def nuke_cache(request):
    if request.user.is_authenticated() and request.user.is_superuser:
        try:
            cache = caches['general']
            cache.clear()
            messages.success(request, 'cache successfully cleared!')
        except InvalidCacheBackendError:
            messages.error(request, 'cache is not set correctly!')
    else:
        messages.error(request, 'Only the admin can clear the cache!')
    return redirect('/')
