import logging

from rest_framework import viewsets, status
from rest_framework.response import Response

from digital_book.models import DigitalBookUserAccess

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

        book_access, created = DigitalBookUserAccess.get_or_create_digital_book_user_access(
            user=user,
            book_key=book_key,
            order_number=order_number
        )

        log.info(">>> book_access: %s", book_access)
        log.info(">>> created: %s", created)

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'book_access': str(book_access),
                'created': str(created)
            }
        )