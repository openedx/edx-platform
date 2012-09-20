from functools import wraps
import copy
import json


def expect_json(view_function):
    @wraps(view_function)
    def expect_json_with_cloned_request(request, *args, **kwargs):
        # cdodge: fix postback errors in CMS. The POST 'content-type' header can include additional information
        # e.g. 'charset', so we can't do a direct string compare
        if request.META['CONTENT_TYPE'].lower().startswith("application/json"):
            cloned_request = copy.copy(request)
            cloned_request.POST = cloned_request.POST.copy()
            cloned_request.POST.update(json.loads(request.body))
            return view_function(cloned_request, *args, **kwargs)
        else:
            return view_function(request, *args, **kwargs)

    return expect_json_with_cloned_request
