from functools import wraps
import copy
import json


def expect_json(view_function):
    @wraps(view_function)
    def expect_json_with_cloned_request(request, *args, **kwargs):
        if request.META['CONTENT_TYPE'] == "application/json":
            cloned_request = copy.copy(request)
            cloned_request.POST = cloned_request.POST.copy()
            cloned_request.POST.update(json.loads(request.raw_post_data))
            return view_function(cloned_request, *args, **kwargs)
        else:
            return view_function(request, *args, **kwargs)

    return expect_json_with_cloned_request
