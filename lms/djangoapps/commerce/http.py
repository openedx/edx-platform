""" HTTP-related entities. """

from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK

from util.json_request import JsonResponse


class DetailResponse(JsonResponse):
    """ JSON response that simply contains a detail field. """

    def __init__(self, message, status=HTTP_200_OK, redirect_url=None):
        data = {'detail': message}
        if redirect_url:
            data['redirect_url'] = redirect_url
        super(DetailResponse, self).__init__(resp_obj=data, status=status)


class InternalRequestErrorResponse(DetailResponse):
    """ Response returned when an internal service request fails. """

    def __init__(self, internal_message):
        message = (
            'Call to E-Commerce API failed. Internal Service Message: [{internal_message}]'
            .format(internal_message=internal_message)
        )
        super(InternalRequestErrorResponse, self).__init__(message=message, status=HTTP_500_INTERNAL_SERVER_ERROR)
