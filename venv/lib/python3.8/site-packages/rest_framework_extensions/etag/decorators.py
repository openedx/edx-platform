import logging
from functools import wraps, WRAPPER_ASSIGNMENTS

from django.utils.http import parse_etags, quote_etag

from rest_framework import status
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework_extensions.exceptions import PreconditionRequiredException

from rest_framework_extensions.utils import prepare_header_name
from rest_framework_extensions.settings import extensions_api_settings

logger = logging.getLogger('django.request')


class ETAGProcessor:
    """Based on https://github.com/django/django/blob/master/django/views/decorators/http.py"""

    def __init__(self, etag_func=None, rebuild_after_method_evaluation=False):
        if not etag_func:
            etag_func = extensions_api_settings.DEFAULT_ETAG_FUNC
        self.etag_func = etag_func
        self.rebuild_after_method_evaluation = rebuild_after_method_evaluation

    def __call__(self, func):
        this = self

        @wraps(func, assigned=WRAPPER_ASSIGNMENTS)
        def inner(self, request, *args, **kwargs):
            return this.process_conditional_request(
                view_instance=self,
                view_method=func,
                request=request,
                args=args,
                kwargs=kwargs,
            )

        return inner

    def process_conditional_request(self,
                                    view_instance,
                                    view_method,
                                    request,
                                    args,
                                    kwargs):
        etags, if_none_match, if_match = self.get_etags_and_matchers(request)
        res_etag = self.calculate_etag(
            view_instance=view_instance,
            view_method=view_method,
            request=request,
            args=args,
            kwargs=kwargs,
        )

        if self.is_if_none_match_failed(res_etag, etags, if_none_match):
            if request.method in SAFE_METHODS:
                response = Response(status=status.HTTP_304_NOT_MODIFIED)
            else:
                response = self._get_and_log_precondition_failed_response(
                    request=request)
        elif self.is_if_match_failed(res_etag, etags, if_match):
            response = self._get_and_log_precondition_failed_response(
                request=request)
        else:
            response = view_method(view_instance, request, *args, **kwargs)
            if self.rebuild_after_method_evaluation:
                res_etag = self.calculate_etag(
                    view_instance=view_instance,
                    view_method=view_method,
                    request=request,
                    args=args,
                    kwargs=kwargs,
                )

        if res_etag and not response.has_header('ETag'):
            response['ETag'] = quote_etag(res_etag)

        return response

    def get_etags_and_matchers(self, request):
        etags = None
        if_none_match = request.META.get(prepare_header_name("if-none-match"))
        if_match = request.META.get(prepare_header_name("if-match"))
        if if_none_match or if_match:
            # There can be more than one ETag in the request, so we
            # consider the list of values.
            try:
                etags = parse_etags(if_none_match or if_match)
            except ValueError:
                # In case of invalid etag ignore all ETag headers.
                # Apparently Opera sends invalidly quoted headers at times
                # (we should be returning a 400 response, but that's a
                # little extreme) -- this is Django bug #10681.
                if_none_match = None
                if_match = None
        return etags, if_none_match, if_match

    def calculate_etag(self,
                       view_instance,
                       view_method,
                       request,
                       args,
                       kwargs):
        if isinstance(self.etag_func, str):
            etag_func = getattr(view_instance, self.etag_func)
        else:
            etag_func = self.etag_func
        return etag_func(
            view_instance=view_instance,
            view_method=view_method,
            request=request,
            args=args,
            kwargs=kwargs,
        )

    def is_if_none_match_failed(self, res_etag, etags, if_none_match):
        if res_etag and if_none_match:
            etags = [etag.strip('"') for etag in etags]
            return res_etag in etags or '*' in etags
        else:
            return False

    def is_if_match_failed(self, res_etag, etags, if_match):
        if res_etag and if_match:
            return res_etag not in etags and '*' not in etags
        else:
            return False

    def _get_and_log_precondition_failed_response(self, request):
        logger.warning('Precondition Failed: %s', request.path,
                       extra={
                           'status_code': status.HTTP_412_PRECONDITION_FAILED,
                           'request': request
                       }
                       )
        return Response(status=status.HTTP_412_PRECONDITION_FAILED)


class APIETAGProcessor(ETAGProcessor):
    """
    This class is responsible for calculating the ETag value given (a list of) model instance(s).

    It does not make sense to compute a default ETag here, because the processor would always issue a 304 response,
    even if the response was modified meanwhile.
    Therefore the `APIETAGProcessor` cannot be used without specifying an `etag_func` as keyword argument.

    According to RFC 6585, conditional headers may be enforced for certain services that support conditional
    requests. For optimistic locking, the server should respond status code 428 including a description on how
    to resubmit the request successfully, see https://tools.ietf.org/html/rfc6585#section-3.
    """

    # require a pre-conditional header (e.g. If-Match) for unsafe HTTP methods (RFC 6585)
    # override this defaults, if required
    precondition_map = {'PUT': ['If-Match'],
                        'PATCH': ['If-Match'],
                        'DELETE': ['If-Match']}

    def __init__(self, etag_func=None, rebuild_after_method_evaluation=False, precondition_map=None):
        assert etag_func is not None, ('None-type functions are not allowed for processing API ETags.'
                                       'You must specify a proper function to calculate the API ETags '
                                       'using the "etag_func" keyword argument.')

        if precondition_map is not None:
            self.precondition_map = precondition_map
        assert isinstance(self.precondition_map, dict), ('`precondition_map` must be a dict, where '
                                                         'the key is the HTTP verb, and the value is a list of '
                                                         'HTTP headers that must all be present for that request.')

        super().__init__(etag_func=etag_func,
                                               rebuild_after_method_evaluation=rebuild_after_method_evaluation)

    def get_etags_and_matchers(self, request):
        """Get the etags from the header and perform a validation against the required preconditions."""
        # evaluate the preconditions, raises 428 if condition is not met
        self.evaluate_preconditions(request)
        # alright, headers are present, extract the values and match the conditions
        return super().get_etags_and_matchers(request)

    def evaluate_preconditions(self, request):
        """Evaluate whether the precondition for the request is met."""
        if request.method.upper() in self.precondition_map.keys():
            required_headers = self.precondition_map.get(
                request.method.upper(), [])
            # check the required headers
            for header in required_headers:
                if not request.META.get(prepare_header_name(header)):
                    # raise an error for each header that does not match
                    logger.warning('Precondition required: %s', request.path,
                                   extra={
                                       'status_code': status.HTTP_428_PRECONDITION_REQUIRED,
                                       'request': request
                                   }
                                   )
                    # raise an RFC 6585 compliant exception
                    raise PreconditionRequiredException(detail='Precondition required. This "%s" request '
                                                               'is required to be conditional. '
                                                               'Try again using "%s".' % (
                                                                   request.method, header)
                                                        )
        return True


etag = ETAGProcessor
api_etag = APIETAGProcessor
