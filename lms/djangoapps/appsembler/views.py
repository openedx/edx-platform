import logging

from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt                                          
from django.contrib.auth.models import User
from django.core.validators import validate_email

from django.core.exceptions import ValidationError
from django.core.mail import send_mail

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.courses import get_course_by_id
from instructor.enrollment import (
    enroll_email,
    get_email_params,
)

#hijack account creation at time of POST
from student.views import _do_create_account
from student.models import create_comments_service_user

#for password/username creation
import random
import string


logger = logging.getLogger(__name__)

@csrf_exempt 
def user_signup_endpoint(request):
    if request.method != 'POST':
        logger.warning('Non-POST request coming to url: /infusionsoft')
        raise Http404

    post_secret = request.POST.get('SecretKey','')
    server_secret = settings.APPSEMBLER_FEATURES.get('APPSEMBLER_SECRET_KEY','')
    if post_secret != server_secret:
        msg = "POST request to Appsembler Academy failed with secret key: {}".format(post_secret)
        logger.error(msg)
        return HttpResponse(status=403)

    # AMC should send a course id, but if not we skip enrollment
    course_id_str = request.POST.get('CourseId','')

    user_email = request.POST.get('Email','')
    if not user_email:
        logger.error('Could not extract Email from POST request')
        return HttpResponse(status=400)

    #auto create student if none exists
    is_account_new = False
    try:
        validate_email(user_email)
        user = User.objects.get(email=user_email)
    except ValidationError:
        logger.error('User email did not validate correctly: {}'.format(email))
        return HttpResponse(status=400)
    except User.DoesNotExist:
        try:
            #from common/djangoapps/student/view.py:create_account
            full_name = request.POST.get('FirstName') + ' ' + request.POST.get('LastName')
            password = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(15))

            #filter out any spaces and punctuation
            username = ''.join(ch for ch in full_name if ch.isalnum())
            #make sure username is unique
            while User.objects.filter(username=username):
                username = username + str(random.randint(1,9))

            post_vars = {
                'username': username,
                'email': user_email,
                'password': password,
                'name': full_name,
                'level_of_education': '',
                'gender': '',
                'mailing_address': '',
                'city': '',
                'country': '',
                'goals': ''
            }
            (user, profile, registration) = _do_create_account(post_vars)
            create_comments_service_user(user)

            user.is_active = True
            user.save()
            
            is_account_new = True
        except: 
            logger.error('User {} not correctly created through /appsembler/user-signup-endpoint'.format(user_email))
    
            subject = 'Error during account creation process on acadey.appsembler.com'
            message = '''
                Account creation failed for the user with email: {}
            '''.format(user_email)
            send_mail(subject, message, 'support@appsembler.com', ['support@appsembler.com'], fail_silently=False)
    
            return HttpResponse(status=400)

    ##based on students_update_enrollment() in  djangoapps/instructor/views/api.py
    if len(course_id_str) > 0:
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id_str)
        course = get_course_by_id(course_id)
        action = 'enroll'
        auto_enroll = True
        # #send default email only if account wasn't just created -- why?
        # email_students = not is_account_new

    email_params = {} 
    if email_students:
        email_params = get_email_params(course, auto_enroll, secure=request.is_secure())

    # First try to get a user object based on email address
    user = None 
    email = None 
    # language = None 
    try: 
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        email = user_email
    else:
        email = user.email
        # language = get_user_email_language(user)

    try: 
        # Use django.core.validators.validate_email to check email address
        # validity (obviously, cannot check if email actually /exists/,
        # simply that it is plausibly valid)
        validate_email(email)  # Raises ValidationError if invalid

        if action == 'enroll':
            before, after = enroll_email(
                course_id, email, auto_enroll, email_students, email_params 
            )

        if is_account_new:
            course = get_course_by_id(course_id)
            subject = 'Welcome to the BodyMind Institute'
            message = '''
Hello {first_name},
We are delighted to have you on board with us as a student at the BodyMind Institute in the {course_name} Course!
Here is your login information:
Login: http://courses.bodymindinstitute.com
Email: {email}
Password: {password}
If you need any assistance, we would love to hear from you at info@bodymindinstitute.com or by phone toll free at 1-888-787-8886 M-F 9-5pm MST.
Again, welcome!
Your BodyMind Team
www.bodymindinstitute.com
info@bodymindinstitute.com
North America: 1-888-787-8886 M-F 9-5pm MST
Join us in the conversation on Facebook where we regularly host free events, special offers and valuable resources all to enhance your learning with BodyMind Institute.
www.facebook.com/bodymindinstitut
            '''.format(
                    first_name=request.POST.get('FirstName'), 
                    course_name=course.display_name,
                    email=user_email, 
                    password=password
                )
            send_mail(subject, message, 'info@bodymindinstitute.com', [user_email], fail_silently=False)

    except ValidationError:
        # Flag this email as an error if invalid, but continue checking
        # the remaining in the list
        logger.error('User email did not validate correctly: {}'.format(email))
        return HttpResponse(status=400)

    except Exception as exc:  # pylint: disable=broad-except
        # catch and log any exceptions
        # so that one error doesn't cause a 500.
        logger.exception("Error while #{}ing student")
        logger.exception(exc)
        return HttpResponse(status=400)
        

    return HttpResponse(status=200)
