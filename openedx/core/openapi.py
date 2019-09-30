"""
Open API support.
"""

import textwrap

from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# -- Code that will eventually be in another openapi-helpers repo -------------


# Wildcard-import so that users of this module can use
# definitions from drf_yasg.openapi without also importing that module.
from drf_yasg.openapi import *  # pylint: disable=wildcard-import


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


def schema(*args, **kwargs):
    """
    Decorator for documenting an OpenAPI endpoint.

    Identical to `drf_yasg.utils.swagger_auto_schema`__ except that:
    * If in kwargs, operation_description and operation_summary will be
      dedented properly.
    * Otherwise, those fields will be taken from the docstring.
    * Any values in `view_fun._openapi_decorator_data` will be used as
      overrides on kwargs.

    __ https://drf-yasg.readthedocs.io/en/stable/drf_yasg.html#drf_yasg.utils.swagger_auto_schema

    """
    if args and callable(args[0]):
        # decorator may be used with no argument
        return schema(*args[1:], **kwargs)(args[0])

    def decorator(view_func):
        """ Returns the decorated function. """
        # pylint: disable=protected-access
        if view_func.__doc__ is not None:
            doc_lines = view_func.__doc__.strip().split("\n")
            if 'operation_summary' not in kwargs and doc_lines:
                kwargs['operation_summary'] = doc_lines[0].strip()
            if 'operation_description' not in kwargs and len(doc_lines) > 1:
                kwargs['operation_description'] = "\n".join(doc_lines[1:])
        if 'operation_description' in kwargs:
            kwargs['operation_description'] = dedent(kwargs['operation_description'])
        try:
            decorator_data = view_func._openapi_decorator_data
        except AttributeError:
            pass
        else:
            kwargs.update(decorator_data)
        return swagger_auto_schema(**kwargs)(view_func)
    return decorator


def parameter(name, in_, **kwargs):
    """
    Decorator to add information about a paramter to a view function.

    Takes arguments identical to openapi.Parameter.
    Adds data to `view_fun._openapi_decorator_data`.
    Must be used _under_ the @schema decorator. For example:

        @schema
        @parameter('param1', IN_PATH, type=STRING)
        @parameter('param2', IN_PATH, type=INTEGER, description='...')
        def get(self, param1, param2):
            ...
    """
    def decorator(view_func):
        """ Returns the decorated function. """
        # pylint: disable=protected-access
        try:
            decorator_data = view_func._openapi_decorator_data
        except AttributeError:
            decorator_data = view_func._openapi_decorator_data = {}
        new_parameter = openapi.Parameter(name, in_, **kwargs)
        try:
            decorator_data['manual_parameters'].insert(0, new_parameter)
        except KeyError:
            decorator_data['manual_parameters'] = [new_parameter]
        return view_func
    return decorator


def query_parameter(name, **kwargs):
    """
    Identical to paramter(name, IN_QUERY, ...).
    """
    return parameter(name, openapi.IN_QUERY, **kwargs)


def path_parameter(name, **kwargs):
    """
    Identical to paramter(name, IN_PATH, ...).
    """
    return parameter(name, openapi.IN_PATH, **kwargs)


def body_parameter(name, **kwargs):
    """
    Identical to paramter(name, IN_BODY, ...).
    """
    return parameter(name, openapi.IN_BODY, **kwargs)


def form_parameter(name, **kwargs):
    """
    Identical to paramter(name, IN_FORM, ...).
    """
    return parameter(name, openapi.IN_FORM, **kwargs)


def header_parameter(name, **kwargs):
    """
    Identical to paramter(name, IN_HEADER, ...).
    """
    return parameter(name, openapi.IN_HEADER, **kwargs)


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
