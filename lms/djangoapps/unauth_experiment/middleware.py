from django.utils.crypto import get_random_string
from .models import AnonymousUserExpt
from django.db import transaction
from dogapi import dog_stats_api

TEST_COOKIE_NAME = "anonUserTest"

def get_random_anon_username():
    candidate = get_random_string(64)
    while AnonymousUserExpt.objects.filter(username=candidate).exists():
        candidate = get_random_string(64)
    return candidate


class ExperimentalUserMiddleware(object):
    def process_request(self, request):
        # Test if our test anonymous cookie is set
        if not request.COOKIES.get(TEST_COOKIE_NAME):
            with dog_stats_api.timer('unauth_experiment.middleware.add_new_anon_user'):
                with transaction.commit_on_success():
                    anon_username = get_random_anon_username()
                    anon_user = AnonymousUserExpt(username=anon_username,
                                                  user_agent=request.META.get('HTTP_USER_AGENT', ''))
                    anon_user.save()
                # tag request with the username we set, so the response can set the cookie
                request._expt_anon_username = anon_username
            dog_stats_api.increment("unauth_experiment.middleware.new_anon_user")
        return None

    def process_response(self, request, response):
        name_to_set = getattr(request, '_expt_anon_username', None)
        if name_to_set:
            # age is 3 months
            response.set_cookie(TEST_COOKIE_NAME, name_to_set, max_age=7776000)
        return response
