import re
from typing import Any, Optional
from urllib.parse import ParseResult, urlparse

from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin

from corsheaders.conf import conf
from corsheaders.signals import check_request_enabled

ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"
ACCESS_CONTROL_EXPOSE_HEADERS = "Access-Control-Expose-Headers"
ACCESS_CONTROL_ALLOW_CREDENTIALS = "Access-Control-Allow-Credentials"
ACCESS_CONTROL_ALLOW_HEADERS = "Access-Control-Allow-Headers"
ACCESS_CONTROL_ALLOW_METHODS = "Access-Control-Allow-Methods"
ACCESS_CONTROL_MAX_AGE = "Access-Control-Max-Age"


class CorsPostCsrfMiddleware(MiddlewareMixin):
    def _https_referer_replace_reverse(self, request: HttpRequest) -> None:
        """
        Put the HTTP_REFERER back to its original value and delete the
        temporary storage
        """
        if conf.CORS_REPLACE_HTTPS_REFERER and "ORIGINAL_HTTP_REFERER" in request.META:
            http_referer = request.META["ORIGINAL_HTTP_REFERER"]
            request.META["HTTP_REFERER"] = http_referer
            del request.META["ORIGINAL_HTTP_REFERER"]

    def process_request(self, request: HttpRequest) -> None:
        self._https_referer_replace_reverse(request)
        return None

    def process_view(
        self,
        request: HttpRequest,
        callback: Any,
        callback_args: Any,
        callback_kwargs: Any,
    ) -> None:
        self._https_referer_replace_reverse(request)
        return None


class CorsMiddleware(MiddlewareMixin):
    def _https_referer_replace(self, request: HttpRequest) -> None:
        """
        When https is enabled, django CSRF checking includes referer checking
        which breaks when using CORS. This function updates the HTTP_REFERER
        header to make sure it matches HTTP_HOST, provided that our cors logic
        succeeds
        """
        origin = request.META.get("HTTP_ORIGIN")

        if (
            request.is_secure()
            and origin
            and "ORIGINAL_HTTP_REFERER" not in request.META
        ):

            url = urlparse(origin)
            if (
                not conf.CORS_ALLOW_ALL_ORIGINS
                and not self.origin_found_in_white_lists(origin, url)
            ):
                return

            try:
                http_referer = request.META["HTTP_REFERER"]
                http_host = "https://%s/" % request.META["HTTP_HOST"]
                request.META = request.META.copy()
                request.META["ORIGINAL_HTTP_REFERER"] = http_referer
                request.META["HTTP_REFERER"] = http_host
            except KeyError:
                pass

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        If CORS preflight header, then create an
        empty body response (200 OK) and return it

        Django won't bother calling any other request
        view/exception middleware along with the requested view;
        it will call any response middlewares
        """
        request._cors_enabled = self.is_enabled(request)
        if request._cors_enabled:
            if conf.CORS_REPLACE_HTTPS_REFERER:
                self._https_referer_replace(request)

            if (
                request.method == "OPTIONS"
                and "HTTP_ACCESS_CONTROL_REQUEST_METHOD" in request.META
            ):
                response = HttpResponse()
                response["Content-Length"] = "0"
                return response
        return None

    def process_view(
        self,
        request: HttpRequest,
        callback: Any,
        callback_args: Any,
        callback_kwargs: Any,
    ) -> None:
        """
        Do the referer replacement here as well
        """
        if request._cors_enabled and conf.CORS_REPLACE_HTTPS_REFERER:
            self._https_referer_replace(request)
        return None

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """
        Add the respective CORS headers
        """
        enabled = getattr(request, "_cors_enabled", None)
        if enabled is None:
            enabled = self.is_enabled(request)

        if not enabled:
            return response

        patch_vary_headers(response, ["Origin"])

        origin = request.META.get("HTTP_ORIGIN")
        if not origin:
            return response

        try:
            url = urlparse(origin)
        except ValueError:
            return response

        if conf.CORS_ALLOW_CREDENTIALS:
            response[ACCESS_CONTROL_ALLOW_CREDENTIALS] = "true"

        if (
            not conf.CORS_ALLOW_ALL_ORIGINS
            and not self.origin_found_in_white_lists(origin, url)
            and not self.check_signal(request)
        ):
            return response

        if conf.CORS_ALLOW_ALL_ORIGINS and not conf.CORS_ALLOW_CREDENTIALS:
            response[ACCESS_CONTROL_ALLOW_ORIGIN] = "*"
        else:
            response[ACCESS_CONTROL_ALLOW_ORIGIN] = origin

        if len(conf.CORS_EXPOSE_HEADERS):
            response[ACCESS_CONTROL_EXPOSE_HEADERS] = ", ".join(
                conf.CORS_EXPOSE_HEADERS
            )

        if request.method == "OPTIONS":
            response[ACCESS_CONTROL_ALLOW_HEADERS] = ", ".join(conf.CORS_ALLOW_HEADERS)
            response[ACCESS_CONTROL_ALLOW_METHODS] = ", ".join(conf.CORS_ALLOW_METHODS)
            if conf.CORS_PREFLIGHT_MAX_AGE:
                response[ACCESS_CONTROL_MAX_AGE] = str(conf.CORS_PREFLIGHT_MAX_AGE)

        return response

    def origin_found_in_white_lists(self, origin: str, url: ParseResult) -> bool:
        return (
            (origin == "null" and origin in conf.CORS_ALLOWED_ORIGINS)
            or self._url_in_whitelist(url)
            or self.regex_domain_match(origin)
        )

    def regex_domain_match(self, origin: str) -> bool:
        return any(
            re.match(domain_pattern, origin)
            for domain_pattern in conf.CORS_ALLOWED_ORIGIN_REGEXES
        )

    def is_enabled(self, request: HttpRequest) -> bool:
        return bool(
            re.match(conf.CORS_URLS_REGEX, request.path_info)
        ) or self.check_signal(request)

    def check_signal(self, request: HttpRequest) -> bool:
        signal_responses = check_request_enabled.send(sender=None, request=request)
        return any(return_value for function, return_value in signal_responses)

    def _url_in_whitelist(self, url: ParseResult) -> bool:
        origins = [urlparse(o) for o in conf.CORS_ALLOWED_ORIGINS]
        return any(
            origin.scheme == url.scheme and origin.netloc == url.netloc
            for origin in origins
        )
