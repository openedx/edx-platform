import json
import logging

from django.utils.deprecation import MiddlewareMixin
from six import text_type

from lms.djangoapps.discussion.django_comment_client.utils import JsonError
from openedx.core.djangoapps.django_comment_common.comment_client import CommentClientRequestError

log = logging.getLogger(__name__)


class AjaxExceptionMiddleware(MiddlewareMixin):
    """
    Middleware that captures CommentClientRequestErrors during ajax requests
    and tranforms them into json responses
    """
    def process_exception(self, request, exception):
        """
        Processes CommentClientRequestErrors in ajax requests. If the request is an ajax request,
        returns a http response that encodes the error as json
        """
        if isinstance(exception, CommentClientRequestError) and request.is_ajax():
            try:
                return JsonError(json.loads(text_type(exception)), exception.status_code)
            except ValueError:
                return JsonError(text_type(exception), exception.status_code)
        return None
