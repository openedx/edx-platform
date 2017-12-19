"""
Public API for payment processor implementations.
The specific implementation is determined at runtime using Django settings:

    CC_PROCESSOR_NAME: The name of the Python module (in `shoppingcart.processors`) to use.

    CC_PROCESSOR: Dictionary of configuration options for specific processor implementations,
        keyed to processor names.

"""

from django.conf import settings


# Import the processor implementation, using `CC_PROCESSOR_NAME`
# as the name of the Python module in `shoppingcart.processors`
PROCESSOR_MODULE = __import__(
    'shoppingcart.processors.' + settings.CC_PROCESSOR_NAME,
    fromlist=[
        'render_purchase_form_html',
        'process_postpay_callback',
        'get_purchase_endpoint',
        'get_signed_purchase_params',
    ]
)


def render_purchase_form_html(cart, **kwargs):
    """
    Render an HTML form with POSTs to the hosted payment processor.

    Args:
        cart (Order): The order model representing items in the user's cart.

    Returns:
        unicode: the rendered HTML form

    """
    return PROCESSOR_MODULE.render_purchase_form_html(cart, **kwargs)


def process_postpay_callback(params, **kwargs):
    """
    Handle a response from the payment processor.

    Concrete implementations should:
        1) Verify the parameters and determine if the payment was successful.
        2) If successful, mark the order as purchased and call `purchased_callbacks` of the cart items.
        3) If unsuccessful, try to figure out why and generate a helpful error message.
        4) Return a dictionary of the form:
            {'success': bool, 'order': Order, 'error_html': str}

    Args:
        params (dict): Dictionary of parameters received from the payment processor.

    Keyword Args:
        Can be used to provide additional information to concrete implementations.

    Returns:
        dict

    """
    return PROCESSOR_MODULE.process_postpay_callback(params, **kwargs)


def get_purchase_endpoint():
    """
    Return the URL of the current payment processor's endpoint.

    Returns:
        unicode

    """
    return PROCESSOR_MODULE.get_purchase_endpoint()


def get_signed_purchase_params(cart, **kwargs):
    """
    Return the parameters to send to the current payment processor.

    Args:
        cart (Order): The order model representing items in the user's cart.

    Keyword Args:
        Can be used to provide additional information to concrete implementations.

    Returns:
        dict

    """
    return PROCESSOR_MODULE.get_signed_purchase_params(cart, **kwargs)
