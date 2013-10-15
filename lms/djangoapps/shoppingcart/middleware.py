"""
This is the shoppingcart middleware class.
Currently the only middleware is detects whether request.user has a cart that should be displayed in the
navigation.  We want to do this in the middleware to
1) keep database accesses out of templates (this led to a transaction bug with user email changes)
2) because navigation.html is "called" by being included in other templates, there's no "views.py" to put this.
"""
from django.conf import settings
import shoppingcart

class UserHasCartMiddleware(object):
    """
    Detects whether request.user has a cart and sets it as part of the request

    ***
     Because this relies on request.user, it needs to enabled in settings after
     django.contrib.auth.middleware.AuthenticationMiddleware (or equivalent)
    ***
    """
    def process_request(self, request):
        """
        Checks if request has an authenticated user.  If so, checks if request.user has a cart that should
        be displayed.  Anonymous users don't.
        """
        request.display_shopping_cart = False
        if (request.user.is_authenticated() and  # user exists
            settings.MITX_FEATURES.get('ENABLE_PAID_COURSE_REGISTRATION') and  # settings are set
            settings.MITX_FEATURES.get('ENABLE_SHOPPING_CART') and
            shoppingcart.models.Order.user_cart_has_items(request.user)):  # user's cart is non-empty
            request.display_shopping_cart = True
        return None