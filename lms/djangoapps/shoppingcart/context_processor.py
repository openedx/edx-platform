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
    return {'display_shopping_cart': (
        request.user.is_authenticated() and                                # user is logged in and
        settings.FEATURES.get('ENABLE_PAID_COURSE_REGISTRATION') and  # settings enable paid course reg and
        settings.FEATURES.get('ENABLE_SHOPPING_CART') and             # settings enable shopping cart and
        shoppingcart.models.Order.user_cart_has_items(
            request.user,
            shoppingcart.models.PaidCourseRegistration
        )  # user's cart has PaidCourseRegistrations
    )}
