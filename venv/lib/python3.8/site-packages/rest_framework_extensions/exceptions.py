from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class PreconditionRequiredException(APIException):
    status_code = status.HTTP_428_PRECONDITION_REQUIRED
    default_detail = _('This "{method}" request is required to be conditional.')
    default_code = 'precondition_required'
