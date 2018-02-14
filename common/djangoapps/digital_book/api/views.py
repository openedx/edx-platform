import logging

from rest_framework import viewsets, status
from rest_framework.response import Response

from digital_book.models import DigitalBookAccess
from edxmako.shortcuts import render_to_response

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


def digital_book_about(request, book_key_string):
    """
    Display the digital book's about page
    """
    log.info(">>> calling digital_book_about...")
    log.info(">>> request: %s", request)
    log.info(">>> book_key: %s", book_key_string)

    context = {
        'digital_book_key': book_key_string,
        'book_title': book_key_string+" title!", #TODO: make a db of book_keys and titles
        'partner_org': 'PARTNER ORG of ' + book_key_string, #TODO: add this data in db
        'SKU': '8528EDB', #TODO: query ecommerce for sku
    }

    return render_to_response('digital_book_about.html', context)
