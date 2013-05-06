from comment_client import CommentClientError
from django_comment_client.utils import JsonError
import json
import logging

log = logging.getLogger(__name__)


class AjaxExceptionMiddleware(object):
    """
    Middleware that captures CommentClientErrors during ajax requests
    and tranforms them into json responses
    """
    def process_exception(self, request, exception):
        """
        Processes CommentClientErrors in ajax requests. If the request is an ajax request,
        returns a http response that encodes the error as json
        """
        if isinstance(exception, CommentClientError) and request.is_ajax():
            try:
                return JsonError(json.loads(exception.message))
            except ValueError:
                return JsonError(exception.message)
        return None
