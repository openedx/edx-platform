import logging

from rest_framework import viewsets, status
from rest_framework.response import Response

from digital_book.models import DigitalBookAccess

log = logging.getLogger(__name__)


class DigitalBookViewSet(viewsets.GenericViewSet):
    """
    Endpoint in the Digital Book API to grant access of a user to
    a Digital Book
    """

    def create(self, request):

        log.info(">>> request: %s", request)
        log.info(">>> request.data: %s", request.data)

        order_number = request.data['order_number']
        user = request.data['user']
        book_key = request.data['book_key']

        digital_book_access = DigitalBookAccess()

        user_access, created = digital_book_access.get_or_create_digital_book_access(
            username=user,
            book_key=book_key
        )

        log.info(">>> book_access: %s", user_access)
        log.info(">>> created: %s", created)

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'user_access': str(user_access),
                'created': str(created)
            }
        )