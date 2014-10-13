import logging

from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.mail import send_mail

from .utils import get_client_ip
from edxmako.shortcuts import render_to_response, render_to_string
from util.json_request import JsonResponse

log = logging.getLogger(__name__)


@ensure_csrf_cookie
def contact(request):
    if request.method == 'POST':
        if not (request.POST['firstname'] or request.POST['lastname'] or request.POST['email'] or request.POST['message']):
            return render_to_response("static_templates/theme-contact.html", {'error': True})


        ##################################### We will need this #####################################
        # import urllib, urllib2                                                                    #
        #                                                                                           #
        # recaptcha_private_key = '6LfLjfMSAAAAAHPCSEZ3HvMzIYDSXrgA3AFYpQKI'                        #
        #                                                                                           #
        # recaptcha_server_name = 'http://www.google.com/recaptcha/api/verify'                      #
        # recaptcha_server_form = 'https://www.google.com/recaptcha/api/challenge'                  #
        #                                                                                           #
        # client_ip_address = get_client_ip(request)                                                #
        # recaptcha_challenge_field = request.POST['recaptcha_challenge_field']                     #
        # recaptcha_response_field = request.POST['recaptcha_response_field']                       #
        #                                                                                           #
        # params = urllib.urlencode(dict(privatekey=recaptcha_private_key,                          #
        #                            remoteip=client_ip_address,                                    #
        #                            challenge=recaptcha_challenge_field,                           #
        #                            response=recaptcha_response_field))                            #
        #                                                                                           #
        # try:                                                                                      #
        #     data = urllib2.urlopen(recaptcha_server_name, params)                                 #
        #     response = data.read()                                                                #
        #     data.close()                                                                          #
        #     if response:                                                                          #
        #         if response.lower().startswith('true'):                                           #
        #             result = True                                                                 #
        #         else:                                                                             #
        #             params = {'error': True, 'captcha': True}                                     #
        #             return render_to_response("static_templates/theme-contact.html", params)      #
        # except:                                                                                   #
        #     # should return a google error                                                        #
        #     return render_to_response("static_templates/theme-contact.html", {'error': True})     #
        ###################################### Do NOT Delete ########################################


        # send e-mail
        if request.GET['form'] == 'help':
            context = {
                'firstname': request.POST['firstname'],
                'lastname': request.POST['lastname'],
                'email': request.POST['email'],
                'profession': '',
                'interest': '',
                'instorg': '',
                'institution': '',
                'discipline': '',
                'course_title': '',
                'country': '',
                'message': request.POST['message'],
            }
            dest_addr = settings.CONTACT_EMAIL
        else:

            context = {
                'firstname': request.POST['firstname'],
                'lastname': request.POST['lastname'],
                'email': request.POST['email'],
                'profession': request.POST['profession'],
                'interest': request.POST['interest'],
                'instorg': request.POST['instorg'],
                'institution': request.POST['institution'],
                'discipline': request.POST['discipline'],
                'course_title': request.POST['course-title'],
                'country': request.POST['country'],
                'message': request.POST['message'],
            }
            dest_addr = settings.COLLABORATE_EMAIL

        message = render_to_string('contact/email.txt', context)
        subject = 'Request from Edraak.org'
        from_address = request.POST['email']
        js = {}

        try:
            send_mail(subject, message, from_address, [dest_addr], fail_silently=False)
        except Exception:  # pylint: disable=broad-except
            log.warning('Unable to send contact email', exc_info=True)
            js['error'] = 'e-mail not sent...e-mail exception'
            # What is the correct status code to use here? I think it's 500, because
            # the problem is on the server's end -- but also, the account was created.
            # Seems like the core part of the request was successful.
            return JsonResponse(js, status=500)

        return render_to_response("static_templates/theme-contact.html", {'success': True})
    return render_to_response("static_templates/theme-contact.html", {})
