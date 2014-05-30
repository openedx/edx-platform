from django.conf import settings

### Now code that determines, using settings, which actual processor implementation we're using.
processor_name = settings.CC_PROCESSOR.keys()[0]
module = __import__('shoppingcart.processors.' + processor_name,
                    fromlist=['render_purchase_form_html'
                              'process_postpay_callback',
                              'start_payment_process',
                              ])


def render_purchase_form_html(*args, **kwargs):
    """
    The top level call to this module to begin the purchase.
    Given a shopping cart,
    Renders the HTML form for display on user's browser, which POSTS to Hosted Processors
    Returns the HTML as a string
    """
    return module.render_purchase_form_html(*args, **kwargs)


def start_payment_process(*args, **kwargs):
    """
    This top level function is for payment flow where the user clicks - say - a "buy" button
    and needs to call back to Open edX before moving onto payment processor workflows, e.g.
    redirect to different site
    """
    return module.start_payment_process(*args, **kwargs)


def process_postpay_callback(*args, **kwargs):
    """
    The top level call to this module after the purchase.
    This function is handed the callback request after the customer has entered the CC info and clicked "buy"
    on the external payment page.
    It is expected to verify the callback and determine if the payment was successful.
    It returns {'success':bool, 'order':Order, 'error_html':str}
    If successful this function must have the side effect of marking the order purchased and calling the
    purchased_callbacks of the cart items.
    If unsuccessful this function should not have those side effects but should try to figure out why and
    return a helpful-enough error message in error_html.
    """
    return module.process_postpay_callback(*args, **kwargs)
