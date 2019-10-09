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


def schema(parameters=None):
    """
    Decorator for documenting an API endpoint.

    The operation summary and description are taken from the function docstring. All
    description fields should be in Markdown and will be automatically dedented.

    Args:
        parameters (Parameter list): each object may be conveniently defined with the
        `parameter` function.

    This is heavily inspired from the the `drf_yasg.utils.swagger_auto_schema`__
    decorator, but callers do not need to know about this abstraction.

    __ https://drf-yasg.readthedocs.io/en/stable/drf_yasg.html#drf_yasg.utils.swagger_auto_schema
    """
    for param in parameters or ():
        param.description = dedent(param.description)

    def decorator(view_func):
        """
        Final view decorator.
        """
        operation_summary = None
        operation_description = None
        if view_func.__doc__ is not None:
            doc_lines = view_func.__doc__.strip().split("\n")
            if doc_lines:
                operation_summary = doc_lines[0].strip()
            if len(doc_lines) > 1:
                operation_description = dedent("\n".join(doc_lines[1:]))
        return drf_swagger_auto_schema(
            manual_parameters=parameters,
            operation_summary=operation_summary,
            operation_description=operation_description
        )(view_func)
    return decorator


def is_schema_request(request):
    """Is this request serving an OpenAPI schema?"""
    return request.query_params.get('format') == 'openapi'


class ParameterLocation(object):
    """Location of API parameter in request."""
    BODY = openapi.IN_BODY
    PATH = openapi.IN_PATH
    QUERY = openapi.IN_QUERY
    FORM = openapi.IN_FORM
    HEADER = openapi.IN_HEADER


def string_parameter(name, in_, description=None):
    """
    Convenient function for defining a string parameter.

    Args:
        name (str)
        in_ (ParameterLocation attribute)
        description (str)
    """
    return parameter(name, in_, str, description=description)


def parameter(name, in_, param_type, description=None):
    """
    Define typed parameters.

    Args:
        name (str)
        in_ (ParameterLocation attribute)
        type (type): one of object, str, float, int, bool, list, file.
        description (str)
    """
    openapi_type = None
    if param_type is object:
        openapi_type = openapi.TYPE_OBJECT
    elif param_type is str:
        openapi_type = openapi.TYPE_STRING
    elif param_type is float:
        openapi_type = openapi.TYPE_NUMBER
    elif param_type is int:
        openapi_type = openapi.TYPE_INTEGER
    elif param_type is bool:
        openapi_type = openapi.TYPE_BOOLEAN
    elif param_type is list:
        openapi_type = openapi.TYPE_ARRAY
    elif param_type is file:
        openapi_type = openapi.TYPE_FILE
    else:
        raise ValueError(u"Unsupported parameter type: '{}'".format(type))
    return openapi.Parameter(
        name,
        in_,
        type=openapi_type,
        description=description
    )
# -----------------------------------------------------


default_info = openapi.Info(
    title="Open edX API",
    default_version="v1",
    description="APIs for access to Open edX information",
    #terms_of_service="https://www.google.com/policies/terms/",         # TODO: Do we have these?
    contact=openapi.Contact(email="oscm@edx.org"),
    #license=openapi.License(name="BSD License"),                       # TODO: What does this mean?
)

schema_view = get_schema_view(
    default_info,
    generator_class=ApiSchemaGenerator,
    public=True,
    permission_classes=(permissions.AllowAny,),
)
