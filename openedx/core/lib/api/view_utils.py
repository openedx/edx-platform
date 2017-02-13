"""
Utilities related to API views
"""
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError, ObjectDoesNotExist
from django.http import Http404
from django.utils.translation import ugettext as _

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import clone_request
from rest_framework.response import Response
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.generics import GenericAPIView

from edx_rest_framework_extensions.authentication import JwtAuthentication
from openedx.core.lib.api.authentication import (
    SessionAuthenticationAllowInactiveUser,
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import IsUserInUrl


class DeveloperErrorViewMixin(object):
    """
    A view mixin to handle common error cases other than validation failure
    (auth failure, method not allowed, etc.) by generating an error response
    conforming to our API conventions with a developer message.
    """
    def make_error_response(self, status_code, developer_message, error_code=None):
        """
        Build an error response with the given status code and developer_message
        """
        error_data = {"developer_message": developer_message}
        if error_code is not None:
            error_data['error_code'] = error_code
        return Response(error_data, status=status_code)

    def make_validation_error_response(self, validation_error):
        """
        Build a 400 error response from the given ValidationError
        """
        if hasattr(validation_error, "message_dict"):
            response_obj = {}
            message_dict = dict(validation_error.message_dict)
            # Extract both Django form and DRF serializer non-field errors
            non_field_error_list = (
                message_dict.pop(NON_FIELD_ERRORS, []) +
                message_dict.pop("non_field_errors", [])
            )
            if non_field_error_list:
                response_obj["developer_message"] = non_field_error_list[0]
            if message_dict:
                response_obj["field_errors"] = {
                    field: {"developer_message": message_dict[field][0]}
                    for field in message_dict
                }
            return Response(response_obj, status=400)
        else:
            return self.make_error_response(400, validation_error.messages[0])

    def handle_exception(self, exc):
        """
        Generalized helper method for managing specific API exception workflows
        """

        if isinstance(exc, APIException):
            return self.make_error_response(exc.status_code, exc.detail)
        elif isinstance(exc, Http404) or isinstance(exc, ObjectDoesNotExist):
            return self.make_error_response(404, exc.message or "Not found.")
        elif isinstance(exc, ValidationError):
            return self.make_validation_error_response(exc)
        else:
            raise


class ExpandableFieldViewMixin(object):
    """A view mixin to add expansion information to the serializer context for later use by an ExpandableField."""

    def get_serializer_context(self):
        """Adds expand information from query parameters to the serializer context to support expandable fields."""
        result = super(ExpandableFieldViewMixin, self).get_serializer_context()
        result['expand'] = [x for x in self.request.query_params.get('expand', '').split(',') if x]
        return result


def view_auth_classes(is_user=False, is_authenticated=True):
    """
    Function and class decorator that abstracts the authentication and permission checks for api views.
    """
    def _decorator(func_or_class):
        """
        Requires either OAuth2 or Session-based authentication.
        If is_user is True, also requires username in URL matches the request user.
        """
        func_or_class.authentication_classes = (
            JwtAuthentication,
            OAuth2AuthenticationAllowInactiveUser,
            SessionAuthenticationAllowInactiveUser
        )
        func_or_class.permission_classes = ()
        if is_authenticated:
            func_or_class.permission_classes += (IsAuthenticated,)
        if is_user:
            func_or_class.permission_classes += (IsUserInUrl,)
        return func_or_class
    return _decorator


def add_serializer_errors(serializer, data, field_errors):
    """Adds errors from serializer validation to field_errors. data is the original data to deserialize."""
    if not serializer.is_valid():
        errors = serializer.errors
        for key, error in errors.iteritems():
            field_errors[key] = {
                'developer_message': u"Value '{field_value}' is not valid for field '{field_name}': {error}".format(
                    field_value=data.get(key, ''), field_name=key, error=error
                ),
                'user_message': _(u"This value is invalid."),
            }
    return field_errors


def build_api_error(message, **kwargs):
    """Build an error dict corresponding to edX API conventions.

    Args:
        message (string): The string to use for developer and user messages.
            The user message will be translated, but for this to work message
            must have already been scraped. ugettext_noop is useful for this.
        **kwargs: format parameters for message
    """
    return {
        'developer_message': message.format(**kwargs),
        'user_message': _(message).format(**kwargs),  # pylint: disable=translation-of-non-string
    }


class RetrievePatchAPIView(RetrieveModelMixin, UpdateModelMixin, GenericAPIView):
    """Concrete view for retrieving and updating a model instance.

    Like DRF's RetrieveUpdateAPIView, but without PUT and with automatic validation errors in the edX format.
    """
    def get(self, request, *args, **kwargs):
        """Retrieves the specified resource using the RetrieveModelMixin."""
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """Checks for validation errors, then updates the model using the UpdateModelMixin."""
        field_errors = self._validate_patch(request.data)
        if field_errors:
            return Response({'field_errors': field_errors}, status=status.HTTP_400_BAD_REQUEST)
        return self.partial_update(request, *args, **kwargs)

    def _validate_patch(self, patch):
        """Validates a JSON merge patch. Captures DRF serializer errors and converts them to edX's standard format."""
        field_errors = {}
        serializer = self.get_serializer(self.get_object_or_none(), data=patch, partial=True)
        fields = self.get_serializer().get_fields()

        for key in patch:
            if key in fields and fields[key].read_only:
                field_errors[key] = {
                    'developer_message': "This field is not editable",
                    'user_message': _("This field is not editable"),
                }

        add_serializer_errors(serializer, patch, field_errors)

        return field_errors

    def get_object_or_none(self):
        """
        Retrieve an object or return None if the object can't be found.

        NOTE: This replaces functionality that was removed in Django Rest Framework v3.1.
        """
        try:
            return self.get_object()
        except Http404:
            if self.request.method == 'PUT':
                # For PUT-as-create operation, we need to ensure that we have
                # relevant permissions, as if this was a POST request.  This
                # will either raise a PermissionDenied exception, or simply
                # return None.
                self.check_permissions(clone_request(self.request, 'POST'))
            else:
                # PATCH requests where the object does not exist should still
                # return a 404 response.
                raise
