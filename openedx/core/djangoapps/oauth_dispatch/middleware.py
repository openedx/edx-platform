from django.conf import settings


class JwtAuthCookieMiddleware(object):
    def process_request(self, request):
        header_payload_cookie = request.COOKIES.get(
            settings.JWT_AUTH['JWT_AUTH_COOKIE_HEADER_PAYLOAD']
        )
        signature_cookie = request.COOKIES.get(
            settings.JWT_AUTH['JWT_AUTH_COOKIE_SIGNATURE']
        )

        # Reconstitute JWT auth cookie if available.
        if header_payload_cookie and signature_cookie:
            request.COOKIES[settings.JWT_AUTH['JWT_AUTH_COOKIE']] = '{}.{}'.format(
                header_payload_cookie,
                signature_cookie,
            )
