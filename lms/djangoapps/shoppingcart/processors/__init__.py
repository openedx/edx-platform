from django.conf import settings

### Now code that determines, using settings, which actual processor implementation we're using.
processor_name = settings.CC_PROCESSOR.keys()[0]
module = __import__('shoppingcart.processors.' + processor_name,
                    fromlist=['sign',
                              'verify',
                              'render_purchase_form_html'
                              'payment_accepted',
                              'record_purchase',
                              'process_postpay_callback',
                              ])

def render_purchase_form_html(*args, **kwargs):
    """
    The top level call to this module to begin the purchase.
    Given a shopping cart,
    Renders the HTML form for display on user's browser, which POSTS to Hosted Processors
    Returns the HTML as a string
    """
    return module.render_purchase_form_html(*args, **kwargs)

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

def sign(*args, **kwargs):
    """
    Given a dict (or OrderedDict) of parameters to send to the
    credit card processor, signs them in the manner expected by
    the processor

    Returns a dict containing the signature
    """
    return module.sign(*args, **kwargs)

def verify(*args, **kwargs):
    """
    Given a dict (or OrderedDict) of parameters to returned by the
    credit card processor, verifies them in the manner specified by
    the processor

    Returns a boolean
    """
    return module.sign(*args, **kwargs)

def payment_accepted(*args, **kwargs):
    """
    Given params returned by the CC processor, check that processor has accepted the payment
    Returns a dict of {accepted:bool, amt_charged:float, currency:str, order:Order}
    """
    return module.payment_accepted(*args, **kwargs)

def record_purchase(*args, **kwargs):
    """
    Given params returned by the CC processor, record that the purchase has occurred in
    the database and also run callbacks
    """
    return module.record_purchase(*args, **kwargs)

