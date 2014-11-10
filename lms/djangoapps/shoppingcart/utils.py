"""
Utility methods for the Shopping Cart app
"""

from django.conf import settings
from microsite_configuration import microsite


def is_shopping_cart_enabled():
    """
    Utility method to check the various configuration to verify that
    all of the settings have been enabled
    """
    enable_paid_course_registration = microsite.get_value(
        'ENABLE_PAID_COURSE_REGISTRATION',
        settings.FEATURES.get('ENABLE_PAID_COURSE_REGISTRATION')
    )

    enable_shopping_cart = microsite.get_value(
        'ENABLE_SHOPPING_CART',
        settings.FEATURES.get('ENABLE_SHOPPING_CART')
    )

    return (enable_paid_course_registration and enable_shopping_cart)
