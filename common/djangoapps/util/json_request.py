from functools import wraps
import copy
import json
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.http import HttpResponse


def expect_json(view_function):
    """
    View decorator for simplifying handing of requests that expect json.  If the request's
    CONTENT_TYPE is application/json, parses the json dict from request.body, and updates
    request.POST with the contents.
    """
    @wraps(view_function)
    def parse_json_into_request(request, *args, **kwargs):
        # cdodge: fix postback errors in CMS. The POST 'content-type' header can include additional information
        # e.g. 'charset', so we can't do a direct string compare
        if "application/json" in request.META.get('CONTENT_TYPE', ''):
            request.json = json.loads(request.body)
        else:
            request.json = {}

        return view_function(request, *args, **kwargs)

    return parse_json_into_request


class JsonResponse(HttpResponse):
    """
    Django HttpResponse subclass that has sensible defaults for outputting JSON.
    """
    def __init__(self, object=None, status=None, encoder=DjangoJSONEncoder,
                 *args, **kwargs):
        if object in (None, ""):
            content = ""
            status = status or 204
        elif isinstance(object, QuerySet):
            content = serialize('json', object)
        else:
            content = json.dumps(object, cls=encoder, indent=2, ensure_ascii=False)
        kwargs.setdefault("content_type", "application/json")
        if status:
            kwargs["status"] = status
        super(JsonResponse, self).__init__(content, *args, **kwargs)
