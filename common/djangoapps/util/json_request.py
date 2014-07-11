from functools import wraps
import json
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseBadRequest


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
        if "application/json" in request.META.get('CONTENT_TYPE', '') and request.body:
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


class JsonResponseBadRequest(HttpResponseBadRequest):
    """
    Subclass of HttpResponseBadRequest that defaults to outputting JSON.
    Use this to send BadRequestResponse & some Json object along with it.

    Defaults:
        dictionary: empty dictionary
        status: 400
        encoder: DjangoJSONEncoder
    """
    def __init__(self, obj=None, status=400, encoder=DjangoJSONEncoder, *args, **kwargs):
        if obj in (None, ""):
            content = ""
        else:
            content = json.dumps(obj, cls=encoder, indent=2, ensure_ascii=False)
        kwargs.setdefault("content_type", "application/json")
        kwargs["status"] = status
        super(JsonResponseBadRequest, self).__init__(content, *args, **kwargs)
