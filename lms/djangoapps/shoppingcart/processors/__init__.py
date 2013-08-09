from django.conf import settings

### Now code that determines, using settings, which actual processor implementation we're using.
processor_name = settings.CC_PROCESSOR.keys()[0]
module = __import__('shoppingcart.processors.' + processor_name,
                    fromlist=['sign', 'verify', 'render_purchase_form_html'])

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

def render_purchase_form_html(*args, **kwargs):
    """
    Given a shopping cart,
    Renders the HTML form for display on user's browser, which POSTS to Hosted Processors
    Returns the HTML as a string
    """
    return module.render_purchase_form_html(*args, **kwargs)
