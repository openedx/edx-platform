from django.utils.cache import patch_vary_headers
from django.utils import translation
from django.conf import settings


class ForceLangMiddleware(object):
    """
    Ignore Accept-Language HTTP headers and environment LANG variable.

    This will force the I18N machinery to always choose settings.LANGUAGE_CODE
    as the default initial language, unless another one is set via sessions or cookies

    Should be installed *before* any middleware that checks request.META['HTTP_ACCEPT_LANGUAGE'],
    namely django.middleware.locale.LocaleMiddleware
    """
    def process_request(self, request):
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            del request.META['HTTP_ACCEPT_LANGUAGE']
        if 'LANG' in request.environ:
            del request.environ['LANG']


class SessionBasedLocaleMiddleware(object):
    """
    This Middleware saves the desired content language in the user session.
    The SessionMiddleware has to be activated.
    """
    def process_request(self, request):
        if request.method == 'GET' and 'lang' in request.GET:
            if 'language_flag' in request.session and request.session['language_flag']:
                language = request.session['language_reference']
                request.session['language_flag'] = False
            else:
                language = request.GET['lang']
            request.session['language'] = language
        elif 'django_language' in request.session and 'language' in request.POST:
            language = request.POST['language']
            request.session['language_reference'] = request.POST['language']
            request.session['language_flag'] = True
        else:
            language = translation.get_language_from_request(request)

        for lang in settings.LANGUAGES:
            if lang[0] == language:
                translation.activate(language)

        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        patch_vary_headers(response, ('Accept-Language',))
        if 'Content-Language' not in response:
            response['Content-Language'] = translation.get_language()
        translation.deactivate()
        return response
