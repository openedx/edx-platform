"""
Open API support.
"""

import textwrap

from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.utils import swagger_auto_schema as drf_swagger_auto_schema
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# -- Code that will eventually be in another openapi-helpers repo -------------


class ApiSchemaGenerator(OpenAPISchemaGenerator):
    """A schema generator for /api/*

    Only includes endpoints in the /api/* url tree, and sets the path prefix
    appropriately.
    """

    def get_endpoints(self, request):
        endpoints = super(ApiSchemaGenerator, self).get_endpoints(request)
        subpoints = {p: v for p, v in endpoints.items() if p.startswith("/api/")}
        return subpoints

    def determine_path_prefix(self, paths):
        return "/api/"


def dedent(text):
    """
    Dedent multi-line text nicely.

    An initial empty line is ignored so that triple-quoted strings don't need
    to start with a backslash.
    """
    if "\n" in text:
        first, rest = text.split("\n", 1)
        if not first.strip():
            # First line is blank, discard it.
            text = rest
    return textwrap.dedent(text)


def swagger_auto_schema(*args, **kwargs):
    """
    Decorator for documenting an OpenAPI endpoint.

    Identical to `drf_yasg.utils.swagger_auto_schema`__ except that
    description fields will be dedented properly.  All description fields
    should be in Markdown.

    __ https://drf-yasg.readthedocs.io/en/stable/drf_yasg.html#drf_yasg.utils.swagger_auto_schema

    """
    if args:
        if callable(args[0]):
            # decorator may be used with no argument
            return swagger_auto_schema(*args[1:], **kwargs)(args[0])
        raise ValueError("Unsupported positional arguments")

    for param in kwargs.get('manual_parameters', ()):
        param.description = dedent(param.description)

    def decorator(view_func):
        """
        Final view decorator.
        """
        if view_func.__doc__ is not None:
            doc_lines = view_func.__doc__.strip().split("\n")
            if 'operation_summary' not in kwargs and doc_lines:
                kwargs['operation_summary'] = doc_lines[0].strip()
            if 'operation_description' not in kwargs and len(doc_lines) > 1:
                kwargs['operation_description'] = "\n".join(doc_lines[1:])
        if 'operation_description' in kwargs:
            kwargs['operation_description'] = dedent(kwargs['operation_description'])
        return drf_swagger_auto_schema(**kwargs)(view_func)
    return decorator


def is_schema_request(request):
    """Is this request serving an OpenAPI schema?"""
    return request.query_params.get('format') == 'openapi'


# -----------------------------------------------------


openapi_info = openapi.Info(
    title="Open edX API",
    default_version="v1",
    description="APIs for access to Open edX information",
    #terms_of_service="https://www.google.com/policies/terms/",         # TODO: Do we have these?
    contact=openapi.Contact(email="oscm@edx.org"),
    #license=openapi.License(name="BSD License"),                       # TODO: What does this mean?
)

schema_view = get_schema_view(
    openapi_info,
    generator_class=ApiSchemaGenerator,
    public=True,
    permission_classes=(permissions.AllowAny,),
)
