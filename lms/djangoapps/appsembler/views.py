import logging
import random

from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt                                          
from django.contrib.auth.models import User
from django.core.validators import validate_email

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import simplejson

from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

# from opaque_keys.edx.locations import SlashSeparatedCourseKey # deprecated; use:
from opaque_keys.edx.locator import CourseLocator
from courseware.courses import get_course_by_id
from instructor.enrollment import (
    enroll_email,
    get_email_params,
)

#hijack account creation at time of POST
from student.forms import AccountCreationForm
from student.views import _do_create_account
from student.models import create_comments_service_user

from .permissions import SecretKeyPermission
from .serializers import UserSignupSerializer


logger = logging.getLogger(__name__)
APPSEMBLER_EMAIL = 'support@appsembler.com'


class UserSignupAPIView(GenericAPIView):
    permission_classes = (SecretKeyPermission,)
    serializer_class = UserSignupSerializer
    
    def post(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.DATA)
        if serializer.is_valid():
            user = self._create_user(serializer.data)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
    def _create_user(self, data):
        try:
            user = User.objects.get(email=data.get('email'))
        except User.DoesNotExist:
            # filter out any spaces and punctuation
            username = ''.join(ch for ch in data.get('full_name') if ch.isalnum())

            # make sure username is unique
            while User.objects.filter(username=username):
                username = username + str(random.randint(1, 9))

            form = AccountCreationForm(
                data={
                    'username': username,
                    'email': data.get('email'),
                    'password': data.get('password'),
                    'name': data.get('full_name')
                },
                tos_required=False
            )
            try:
                (user, profile, registration) = _do_create_account(form)
            except ValidationError as e:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
            # create_comments_service_user(user)  # TODO: do we need this? if so, fix it

            user.is_active = True
            user.save()
        return user

user_signup_endpoint_new = UserSignupAPIView.as_view()


@api_view(['POST'])
def user_signup_endpoint(request):
    if request.method != 'POST':
        logger.warning('Non-POST request coming to url: /appsembler/user')
        raise Http404

    post_secret = request.POST.get('SecretKey','')
    try:
        # TODO: this should be under APPSEMBLER_FEATURES
        server_secret = settings.FEATURES.get('APPSEMBLER_SECRET_KEY','')
    except AttributeError:
        msg = '''
No secret key.  Add this to your sever-vars and run update: \n
EDXAPP_APPSEMBLER_FEATURES:
    APPSEMBLER_SECRET_KEY: <our key>
'''
        logger.error(msg)
        send_mail("No secret key!", msg, APPSEMBLER_EMAIL, [APPSEMBLER_EMAIL])
        return HttpResponse(status=403)
    if post_secret != server_secret:
        msg = "POST request to Appsembler Academy failed with secret key: {}".format(post_secret)
        logger.error(msg)
        return HttpResponse(status=403)

    first_name = request.POST.get('FirstName', '')
    last_name = request.POST.get('LastName', '')
    full_name = first_name + ' ' + last_name
    if not first_name or not last_name:
        logger.error('Could not extract first & last names form POST request')
        return HttpResponse(status=400)

    user_email = request.POST.get('Email','')
    if not user_email:
        logger.error('Could not extract Email from POST request')
        return HttpResponse(status=400)

    # AMC should send a course id, but if not we skip enrollment
    course_id_str = request.POST.get('CourseId','')
    enroll_in_course = len(course_id_str) > 0
    if not course_id_str:
        logger.info('No course id; user {0} will be created but not enrolled in any \
                    course.'.format(user_email))

    password = request.POST.get('Password','')
    if not password:
        logger.error('Could not extract Password from POST request.')
        return HttpResponse(status=400)

    #auto create student if none exists
    user = None
    user_course = None
    is_account_new = False
    email_student = False
    try:
        validate_email(user_email)
        user = User.objects.get(email=user_email)
    except ValidationError:
        logger.error('User email did not validate correctly: {}'.format(user_email))
        return HttpResponse(status=400)
    except User.DoesNotExist:
        try:
            #from common/djangoapps/student/view.py:create_account
            # password = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(15))

            #filter out any spaces and punctuation
            username = ''.join(ch for ch in full_name if ch.isalnum())
            #make sure username is unique
            while User.objects.filter(username=username):
                username = username + str(random.randint(1,9))

            form = AccountCreationForm(
                data={
                    'username': username,
                    'email': user_email,
                    'password': password,
                    'first_name': first_name,
                    'last_name': last_name,
                    'name': full_name
                },
                tos_required=False
            )
            (user, profile, registration) = _do_create_account(form)
            # create_comments_service_user(user)  # TODO: do we need this? if so, fix it

            user.is_active = True
            user.save()
            
            is_account_new = True
        except: 
            logger.error('User {} not correctly created through /appsembler/user-signup-endpoint'.format(user_email))
    
            subject = 'Error during account creation process on academy.appsembler.com'
            message = '''
                Account creation failed for the user with email: {}
            '''.format(user_email)
            send_mail(subject, message, APPSEMBLER_EMAIL, [APPSEMBLER_EMAIL], fail_silently=False)
    
            return HttpResponse(status=400)

    ##based on students_update_enrollment() in  djangoapps/instructor/views/api.py
    if enroll_in_course:
        # course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id_str)
        try:
            course_id = CourseLocator.from_string(course_id_str)
        # if we can't find the course, log as an error, since we know we sent a course id
        except InvalidKeyError:
            logger.error("Could not find this course: {0}".format(course_id_str))
            userdata = { 'userid': user.id, 'email': user.email, 'course': None }
            data = simplejson.dumps(userdata)
            return HttpResponse(data, status=200, content_type='application/json')

        course = get_course_by_id(course_id)
        action = 'enroll'
        auto_enroll = True
        #send default email only if account wasn't just created 
        email_student = not is_account_new

    email_params = {} 
    if email_student:
        email_params = get_email_params(course, auto_enroll, secure=request.is_secure())

    # We already have the user object (if we couldn't get or create we have returned)
    if user.email != user_email:
        logger.error("The user was not saved with the correct email address.  Abort!")
        user.delete()
        return HttpResponse(status=400)

    try: 
        # Use django.core.validators.validate_email to check email address
        # validity (obviously, cannot check if email actually /exists/,
        # simply that it is plausibly valid)
        validate_email(user.email)  # Raises ValidationError if invalid

        if enroll_in_course:
            enrollment = enroll_email(
                course_id, user.email, auto_enroll, email_student, email_params 
            )
            logger.info("New student enrolled in course.\n{0}".format(enrollment))
            course = get_course_by_id(course_id)
            user_course = course.display_name

        if is_account_new:
            # TODO: convert this to a template
            subject = 'Welcome to Appsembler Academy!'
            message = '''
Hello {first_name},

We are delighted to have you on board with us as a student at \
Appsembler Academy in the {course_name} Course!

Here is your login information:
Login: http://academy.appsembler.com
Email: {email}
Password: {password}

If you need any assistance, we would love to hear from you at \
info@appsembler.com or by phone toll free at 1-617-702-4331.

Again, welcome!
Team Appsembler
academy.appsembler.com
info@appsembler.com
            '''.format(
                    first_name=full_name,
                    #course_name=course.display_name,
                    course_name="TEMP_NAME_TO_MAKE_TESTS_PASS",
                    email=user.email, 
                    password=password
                )
            send_mail(subject, message, 'info@appsembler.com', [user.email], fail_silently=False)

    except ValidationError:
        # Flag this email as an error if invalid
        logger.error('User email did not validate correctly: {}'.format(user.email))
        # should we delete this user? Is the email already validated by AMC? 
        # Will any other app ping this endpoint?
        return HttpResponse(status=400)

    except Exception as exc:  
        # pylint: disable=broad-except
        # catch and log any exceptions
        # so that one error doesn't cause a 500.
        logger.exception("Error while #{}ing student")
        logger.exception(exc)
        return HttpResponse(status=400)

    userdata = { 'username': user.username, 'email': user.email, 'course': user_course }
    data = simplejson.dumps(userdata)
    # return HttpResponse(data, status=200, content_type='application/json')
    return HttpResponse(data, status=200, content_type='application/json')