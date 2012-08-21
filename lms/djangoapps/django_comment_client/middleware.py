from comment_client import CommentClientError
from django_comment_client.utils import JsonError
import json

class AjaxExceptionMiddleware(object): 
    def process_exception(self, request, exception):
        import pdb; pdb.set_trace()
        if isinstance(exception, CommentClientError) and request.is_ajax():
            return JsonError(json.loads(exception.message))
        return None
