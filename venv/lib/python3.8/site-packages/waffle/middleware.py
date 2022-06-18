from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import smart_str

from waffle.utils import get_setting


class WaffleMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        secure = get_setting('SECURE')
        max_age = get_setting('MAX_AGE')

        if hasattr(request, 'waffles'):
            for k in request.waffles:
                name = smart_str(get_setting('COOKIE') % k)
                active, rollout = request.waffles[k]
                if rollout and not active:
                    # "Inactive" is a session cookie during rollout mode.
                    age = None
                else:
                    age = max_age
                response.set_cookie(name, value=active, max_age=age,
                                    secure=secure)
        if hasattr(request, 'waffle_tests'):
            for k in request.waffle_tests:
                name = smart_str(get_setting('TEST_COOKIE') % k)
                value = request.waffle_tests[k]
                response.set_cookie(name, value=value)

        return response
