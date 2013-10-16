"""
This is the shoppingcart context_processor module.
Currently the only context_processor detects whether request.user has a cart that should be displayed in the
navigation.  We want to do this in the context_processor to
1) keep database accesses out of templates (this led to a transaction bug with user email changes)
2) because navigation.html is "called" by being included in other templates, there's no "views.py" to put this.
"""
from django.conf import settings
import shoppingcart


def user_has_cart_context_processor(request):
    """
    Checks if request has an authenticated user.  If so, checks if request.user has a cart that should
    be displayed.  Anonymous users don't.
    Adds `display_shopping_cart` to the context
    """
    display_shopping_cart = False
    if (
        request.user.is_authenticated() and                                # user exists
        settings.MITX_FEATURES.get('ENABLE_PAID_COURSE_REGISTRATION') and  # settings is set
        settings.MITX_FEATURES.get('ENABLE_SHOPPING_CART') and             # setting is set
        shoppingcart.models.Order.user_cart_has_items(request.user)        # user's cart is non-empty
    ):
        display_shopping_cart = True
    return {'display_shopping_cart': display_shopping_cart}
