""" Error codes and exceptions for ESG """
from rest_framework import serializers
from rest_framework.response import Response


# Catch-all error if we don't supply anything
ERR_UNKNOWN = "ERR_UNKNOWN"

# A request is missing a required query param
ERR_MISSING_PARAM = "ERR_MISSING_PARAM"

# The requested ORA_LOCATION could not be found in the course
ERR_BAD_ORA_LOCATION = "ERR_BAD_ORA_LOCATION"

# User tried to operate on a submission that they do not have a lock for
ERR_LOCK_CONTESTED = "ERR_LOCK_CONTESTED"

# Error submitting grade
ERR_GRADE_SUBMIT = "ERR_GRADE_SUBMIT"

# Contested grade
ERR_GRADE_CONTESTED = "ERR_GRADE_CONTESTED"


class LockContestedError(Exception):
    """ Signal for trying to operate on a lock owned by someone else """


class ErrorSerializer(serializers.Serializer):
    """ Returns error code and unpacks additional context """
    error = serializers.CharField(default=ERR_UNKNOWN)

    def to_representation(self, instance):
        """ Override to unpack context alongside error code """
        output = super().to_representation(instance)
        for key, value in self.context.items():
            output[key] = value

        return output


class StaffGraderErrorResponse(Response):
    """ An HTTP error response that returns serialized error data with additional provided context """
    status = 500
    err_code = ERR_UNKNOWN

    def __init__(self, context={}):
        # Unpack provided content into error structure
        content = ErrorSerializer({"error": self.err_code}, context=context).data
        super().__init__(content, status=self.status)


class BadOraLocationResponse(StaffGraderErrorResponse):
    """ An HTTP 400 that returns serialized error data with additional provided context """
    status = 400
    err_code = ERR_BAD_ORA_LOCATION


class MissingParamResponse(StaffGraderErrorResponse):
    """ An HTTP 400 that returns serialized error data with additional provided context """
    status = 400
    err_code = ERR_MISSING_PARAM


class SubmitGradeErrorResponse(StaffGraderErrorResponse):
    """ An HTTP 500 that returns serialized error data with additional provided context """
    status = 500
    err_code = ERR_GRADE_SUBMIT


class LockContestedResponse(StaffGraderErrorResponse):
    """ An HTTP 409 that returns serialized error data with additional provided context """
    status = 409
    err_code = ERR_LOCK_CONTESTED


class GradeContestedResponse(StaffGraderErrorResponse):
    """ An HTTP 409 that returns error data with updated submission status """
    status = 409
    err_code = ERR_GRADE_CONTESTED


class UnknownErrorResponse(StaffGraderErrorResponse):
    """ An HTTP 500 for unknown error types """
    status = 500
    err_code = ERR_UNKNOWN
