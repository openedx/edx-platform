import logging

from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse
from rest_framework import viewsets, status
from rest_framework.response import Response

from digital_book.models import DigitalBookAccess
from digital_book.api.exceptions import DigitalBookAccessRedirect
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


def digital_book_content(request, book_key_string):
    # TODO: ultimately this will redirect the user to a book represented by 'book_key_string'
    """
    For now: serves up book content (represented by a simple HTML page) if user is authenticated
    and has access to this book.  If a user does not have access to the book, they will be redirected
    to the digital book about page.
    """
    import pdb; pdb.set_trace()
    log.info(">>> calling digital_book_content")
    log.info(">>> request: %s", request)
    log.info(">>> book_key: %s", book_key_string)

    log.info(">>> authenticating user...")
    if not (request.user.is_authenticated()):
        return redirect_to_login(request.get_full_path())

    try:
        has_access(request.user, book_key_string)

        context = {
            'book_title': book_key_string,
            'username': request.user,
        }

        return render_to_response('digital_book/digital_book_content.html', context)

    except Exception as exception:
        return None


def digital_book_about(request, book_key_string):
    """
    Display the digital book's about page
    """
    log.info(">>> calling digital_book_about...")
    log.info(">>> request: %s", request)
    log.info(">>> book_key: %s", book_key_string)

    # TODO: query ecommerce for sku
    sku = '8528EDB'
    #TODO: generate basket url dynamically
        #TODO: dynamically get lms base url
        #TODO: dynamically add the sku
        #TODO: pull this out into its own function
    basket_url = 'http://localhost:18130/basket/single-item/?sku={sku}'.format(
        sku=sku
    )

    log.info(">>> basket_url: %s", basket_url)

    context = {
        'digital_book_key': book_key_string,
        'book_title': book_key_string+" title!", #TODO: make a db of book_keys and titles
        'partner_org': 'PARTNER ORG of ' + book_key_string, #TODO: add this data in db
        'basket_url': basket_url,
        'price': 100, #TODO: ask ecommerce for price
    }

    return render_to_response('digital_book/digital_book_about.html', context)


def has_access(username, digital_book_key):

    digital_book_access = DigitalBookAccess()
    if not digital_book_access.has_access(username, digital_book_key):
        raise DigitalBookAccessRedirect(reverse('about_digital_book', args=[digital_book_key]))
