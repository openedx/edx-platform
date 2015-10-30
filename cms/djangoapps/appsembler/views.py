import logging

from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt                                          
from django.contrib.auth.models import User

from django.core.mail import send_mail
from django.utils import simplejson

from rest_framework.decorators import api_view

from cms.djangoapps.contentstore.utils import reverse_course_url
from cms.djangoapps.contentstore.views.course import create_new_course_in_store
from xmodule.modulestore.django import modulestore


logger = logging.getLogger(__name__)
APPSEMBLER_EMAIL = 'support@appsembler.com'


@api_view
def create_course_endpoint(request):
    if request.method != 'POST':
        logger.warning('Non-POST request coming to url: /appsemblerstudio')
        raise Http404
    try:
        post_secret = request.POST.get('SecretKey','')
        print "secret key: {}".format(post_secret)
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



        user_email = request.POST.get('Email','')
        if not user_email:
            logger.error('Could not extract user email from POST request')
            return HttpResponse(status=400)

        # get the user; if no user, return the error
        user = None
        new_course = None
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            message = "User does not exist in academy.appsembler.com."
            send_back = {
                message:message,
                user_email:user_email
            }
            data = simplejson.dumps(send_back)
            return HttpResponse(data, status_code=403, content_type="application/json")

        try:
            store_for_new_course = modulestore().default_modulestore.get_modulestore_type()
            org = "AppsemblerX"
            number = "{}101".format(user.username)
            run = "CurrentTerm"
            fields = {"display_name":"Your First Course"}
            new_course = create_new_course_in_store(store_for_new_course, user, org, 
                                                    number, run, fields)

        except:
            message = "Unable to create new course."
            logger.error(message)

        # course_key = unicode(new_course.id,
        new_course_url = reverse_course_url('course_handler', new_course.id)
        userdata = { 'userid': user.id, 'new_course_url': new_course_url }
        data = simplejson.dumps(userdata)
        return HttpResponse(data, status=200, content_type='application/json')

    except Exception as exc:  
        # pylint: disable=broad-except
        # catch and log any exceptions
        # so that one error doesn't cause a 500.
        logger.exception("Error while #{}ing student")
        logger.exception(exc)
        return HttpResponse(status=400)