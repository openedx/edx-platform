import logging

from rest_framework import viewsets, status
from rest_framework.response import Response

log = logging.getLogger(__name__)


class DigitalBookViewSet(viewsets.GenericViewSet):
    """
    Endpoint in the Digital Book API to grant access of a user to
    a Digital Book
    """

    def create(self, request):
        #TODO: serialize data coming in
        log.info(">>> request: %s", request)
        log.info(">>> request.data: %s", request.data)

        order_number = request.data['order_number']
        user = request.data['user']
        book_key = request.data['book_key']

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'string_data': "very useful unique data",
                'num_data': 42,
            }
        )