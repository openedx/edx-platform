import hashlib
import urllib
from django.http import HttpResponseServerError
import simplejson
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from httplib2 import Http
import logging
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from simplejson.scanner import JSONDecodeError

from edxmako.shortcuts import render_to_response, render_to_string
from util.json_request import JsonResponse
from microsite_configuration import microsite
from .models import BaytPublishedCertificate

log = logging.getLogger(__name__)


@require_POST
@login_required
def get_student_email(request):
    user_email = request.POST['bayt_email']
    course_name = request.POST['course_name']
    course_id = request.POST['course_id']
    user_id = request.user.id

    try:
        validate_email(user_email)
    except ValidationError:
        return JsonResponse({"success": False, "error": _('Invalid Email')})

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        ## close the pop-up because there is sth wrong
        return JsonResponse({"success": False, "error": 'Invalid ID'})
    if user.email == user_email:
        h = Http()
        param = {
            'secret_key': settings.BAYT_SECRET_KEY,
            'valid_until': '06-2015',
            'certificate_name': course_name.encode('UTF-8'),
            'email_address': user_email
        }
        url = "https://api.bayt.com/api/edraak-api/post.adp?" + urllib.urlencode(param)
        print url
        resp, content = h.request(url)
        json_content = simplejson.loads(content)
        if json_content['status'] == "NOT EXISTS":
            return JsonResponse({"success": True, "error": False, "redirect_to": True, "response": content})
        else:
            BaytPublishedCertificate.objects.create(user_id=int(user_id), course_id=course_id)
            return JsonResponse({"success": True, "error": False, "redirect_to": False, "response": content})
    else:
        secret_key = settings.BAYT_SECRET_KEY
        my_string = user_email + course_name + secret_key
        access_token = hashlib.md5(my_string.encode('UTF-8')).hexdigest()
        param = {
            'email': user_email,
            'course_name': course_name.encode('UTF-8'),
            'access_token': access_token,
            'course_id': course_id.encode('UTF-8'),
            'user_id': user_id
        }
        if not settings.DEBUG:
            url = "https://edraak.org/bayt-activation?" + urllib.urlencode(param)
        else:
            url = request.META['HTTP_HOST'] + "/bayt-activation?" + urllib.urlencode(param)
        context = {
            'encoded_url': url
        }
        message = render_to_string('bayt/verification_email.txt', context)
        if not (settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING')):
            from_address = microsite.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
            try:
                send_mail('Bayt Edraak Verification', message, from_address, [user_email], fail_silently=False)
                # here we have to send an auth email to user email that contains a link to
                # get back to here and then post the certificate
                return JsonResponse({"success": True, "error": False, "redirect_to": False})
            except:
                log.warning('Unable to send activation email to user', exc_info=True)
                return JsonResponse({"success": False, "error": True, "redirect_to": False})
        else:
            return JsonResponse({"success": False, "error": True, "redirect_to": False})

@login_required
def activation(request):
    access_token = request.GET['access_token']
    user_email = request.GET['email']
    course_name = request.GET['course_name']
    course_id = request.GET['course_id']
    user_id = request.user.id
    secret_key = settings.BAYT_SECRET_KEY
    my_string = user_email + course_name + secret_key
    current_access_token = hashlib.md5(my_string.encode('UTF-8')).hexdigest()
    if current_access_token == access_token:
        h = Http()
        param = {
            'secret_key': settings.BAYT_SECRET_KEY,
            'valid_until': '06-2015',
            'certificate_name': course_name.encode('UTF-8'),
            'email_address': user_email
        }
        url = "https://api.bayt.com/api/edraak-api/post.adp?" + urllib.urlencode(param)
        resp, content = h.request(url)

        json_content = simplejson.loads(content)

        if json_content['status'] == "NOT EXISTS":
            # redirect user to bayt registration
            return render_to_response("bayt/callback.html", {"status": False})
        BaytPublishedCertificate.objects.create(user_id=user_id, course_id=course_id)
        return render_to_response("bayt/callback.html", {"status": True})
    else:
        return JsonResponse({"success": False, "error": True, "redirect_to": False})
