""" HTTP-related entities. """

from rest_framework.status import HTTP_503_SERVICE_UNAVAILABLE, HTTP_200_OK

from util.json_request import JsonResponse


class DetailResponse(JsonResponse):
    """ JSON response that simply contains a detail field. """

    def __init__(self, message, status=HTTP_200_OK):
        data = {'detail': message}
        super(DetailResponse, self).__init__(object=data, status=status)


class ApiErrorResponse(DetailResponse):
    """ Response returned when calls to the E-Commerce API fail or the returned data is invalid. """

    def __init__(self):
        message = 'Call to E-Commerce API failed. Order creation failed.'
        super(ApiErrorResponse, self).__init__(message=message, status=HTTP_503_SERVICE_UNAVAILABLE)
