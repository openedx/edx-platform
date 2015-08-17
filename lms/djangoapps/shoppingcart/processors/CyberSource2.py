"""
Implementation of the CyberSource credit card processor using the newer "Secure Acceptance API".
The previous Hosted Order Page API is being deprecated as of 9/14.

For now, we're keeping the older implementation in the code-base so we can
quickly roll-back by updating the configuration.  Eventually, we should replace
the original implementation with this version.

To enable this implementation, add the following Django settings:

    CC_PROCESSOR_NAME = "CyberSource2"
    CC_PROCESSOR = {
        "CyberSource2": {
            "SECRET_KEY": "<secret key>",
            "ACCESS_KEY": "<access key>",
            "PROFILE_ID": "<profile ID>",
            "PURCHASE_ENDPOINT": "<purchase endpoint>"
        }
    }

"""

import hmac
import binascii
import re
import json
import uuid
import logging
from textwrap import dedent
from datetime import datetime
from collections import OrderedDict, defaultdict
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from django.conf import settings
from django.utils.translation import ugettext as _, ugettext_noop
from edxmako.shortcuts import render_to_string
from shoppingcart.models import Order
from shoppingcart.processors.exceptions import *
from shoppingcart.processors.helpers import get_processor_config
from microsite_configuration import microsite

log = logging.getLogger(__name__)

# Translators: this text appears when an unfamiliar error code occurs during payment,
# for which we don't know a user-friendly message to display in advance.
DEFAULT_REASON = ugettext_noop("UNKNOWN REASON")


def process_postpay_callback(params):
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
    try:
        valid_params = verify_signatures(params)
        result = _payment_accepted(
            valid_params['req_reference_number'],
            valid_params['auth_amount'],
            valid_params['req_currency'],
            valid_params['decision']
        )
        if result['accepted']:
            _record_purchase(params, result['order'])
            return {
                'success': True,
                'order': result['order'],
                'error_html': ''
            }
        else:
            _record_payment_info(params, result['order'])
            return {
                'success': False,
                'order': result['order'],
                'error_html': _get_processor_decline_html(params)
            }
    except CCProcessorException as error:
        log.exception('error processing CyberSource postpay callback')
        # if we have the order and the id, log it
        if hasattr(error, 'order'):
            _record_payment_info(params, error.order)
        else:
            log.info(json.dumps(params))
        return {
            'success': False,
            'order': None,  # due to exception we may not have the order
            'error_html': _get_processor_exception_html(error)
        }


def processor_hash(value):
    """
    Calculate the base64-encoded, SHA-256 hash used by CyberSource.

    Args:
        value (string): The value to encode.

    Returns:
        string

    """
    secret_key = get_processor_config().get('SECRET_KEY', '')
    hash_obj = hmac.new(secret_key.encode('utf-8'), value.encode('utf-8'), sha256)
    return binascii.b2a_base64(hash_obj.digest())[:-1]  # last character is a '\n', which we don't want


def verify_signatures(params):
    """
    Use the signature we receive in the POST back from CyberSource to verify
    the identity of the sender (CyberSource) and that the contents of the message
    have not been tampered with.

    Args:
        params (dictionary): The POST parameters we received from CyberSource.

    Returns:
        dict: Contains the parameters we will use elsewhere, converted to the
            appropriate types

    Raises:
        CCProcessorSignatureException: The calculated signature does not match
            the signature we received.

        CCProcessorDataException: The parameters we received from CyberSource were not valid
            (missing keys, wrong types)

    """

    # First see if the user cancelled the transaction
    # if so, then not all parameters will be passed back so we can't yet verify signatures
    if params.get('decision') == u'CANCEL':
        raise CCProcessorUserCancelled()

    #  if the user decline the transaction
    # if so, then auth_amount will not be passed back so we can't yet verify signatures
    if params.get('decision') == u'DECLINE':
        raise CCProcessorUserDeclined()

    # Validate the signature to ensure that the message is from CyberSource
    # and has not been tampered with.
    signed_fields = params.get('signed_field_names', '').split(',')
    data = u",".join([u"{0}={1}".format(k, params.get(k, '')) for k in signed_fields])
    returned_sig = params.get('signature', '')
    if processor_hash(data) != returned_sig:
        raise CCProcessorSignatureException()

    # Validate that we have the paramters we expect and can convert them
    # to the appropriate types.
    # Usually validating the signature is sufficient to validate that these
    # fields exist, but since we're relying on CyberSource to tell us
    # which fields they included in the signature, we need to be careful.
    valid_params = {}
    required_params = [
        ('req_reference_number', int),
        ('req_currency', str),
        ('decision', str),
        ('auth_amount', Decimal),
    ]
    for key, key_type in required_params:
        if key not in params:
            raise CCProcessorDataException(
                _(
                    u"The payment processor did not return a required parameter: {parameter}"
                ).format(parameter=key)
            )
        try:
            valid_params[key] = key_type(params[key])
        except (ValueError, TypeError, InvalidOperation):
            raise CCProcessorDataException(
                _(
                    u"The payment processor returned a badly-typed value {value} for parameter {parameter}."
                ).format(value=params[key], parameter=key)
            )

    return valid_params


def sign(params):
    """
    Sign the parameters dictionary so CyberSource can validate our identity.

    The params dict should contain a key 'signed_field_names' that is a comma-separated
    list of keys in the dictionary.  The order of this list is important!

    Args:
        params (dict): Dictionary of parameters; must include a 'signed_field_names' key

    Returns:
        dict: The same parameters dict, with a 'signature' key calculated from the other values.

    """
    fields = u",".join(params.keys())
    params['signed_field_names'] = fields

    signed_fields = params.get('signed_field_names', '').split(',')
    values = u",".join([u"{0}={1}".format(i, params.get(i, '')) for i in signed_fields])
    params['signature'] = processor_hash(values)
    params['signed_field_names'] = fields

    return params


def render_purchase_form_html(cart, callback_url=None, extra_data=None):
    """
    Renders the HTML of the hidden POST form that must be used to initiate a purchase with CyberSource

    Args:
        cart (Order): The order model representing items in the user's cart.

    Keyword Args:
        callback_url (unicode): The URL that CyberSource should POST to when the user
            completes a purchase.  If not provided, then CyberSource will use
            the URL provided by the administrator of the account
            (CyberSource config, not LMS config).

        extra_data (list): Additional data to include as merchant-defined data fields.

    Returns:
        unicode: The rendered HTML form.

    """
    return render_to_string('shoppingcart/cybersource_form.html', {
        'action': get_purchase_endpoint(),
        'params': get_signed_purchase_params(
            cart, callback_url=callback_url, extra_data=extra_data
        ),
    })


def get_signed_purchase_params(cart, callback_url=None, extra_data=None):
    """
    This method will return a digitally signed set of CyberSource parameters

    Args:
        cart (Order): The order model representing items in the user's cart.

    Keyword Args:
        callback_url (unicode): The URL that CyberSource should POST to when the user
            completes a purchase.  If not provided, then CyberSource will use
            the URL provided by the administrator of the account
            (CyberSource config, not LMS config).

        extra_data (list): Additional data to include as merchant-defined data fields.

    Returns:
        dict

    """
    return sign(get_purchase_params(cart, callback_url=callback_url, extra_data=extra_data))


def get_purchase_params(cart, callback_url=None, extra_data=None):
    """
    This method will build out a dictionary of parameters needed by CyberSource to complete the transaction

    Args:
        cart (Order): The order model representing items in the user's cart.

    Keyword Args:
        callback_url (unicode): The URL that CyberSource should POST to when the user
            completes a purchase.  If not provided, then CyberSource will use
            the URL provided by the administrator of the account
            (CyberSource config, not LMS config).

        extra_data (list): Additional data to include as merchant-defined data fields.

    Returns:
        dict

    """
    total_cost = cart.total_cost
    amount = "{0:0.2f}".format(total_cost)
    params = OrderedDict()

    params['amount'] = amount
    params['currency'] = cart.currency
    params['orderNumber'] = "OrderId: {0:d}".format(cart.id)

    params['access_key'] = get_processor_config().get('ACCESS_KEY', '')
    params['profile_id'] = get_processor_config().get('PROFILE_ID', '')
    params['reference_number'] = cart.id
    params['transaction_type'] = 'sale'

    params['locale'] = 'en'
    params['signed_date_time'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    params['signed_field_names'] = 'access_key,profile_id,amount,currency,transaction_type,reference_number,signed_date_time,locale,transaction_uuid,signed_field_names,unsigned_field_names,orderNumber'
    params['unsigned_field_names'] = ''
    params['transaction_uuid'] = uuid.uuid4().hex
    params['payment_method'] = 'card'

    if callback_url is not None:
        params['override_custom_receipt_page'] = callback_url
        params['override_custom_cancel_page'] = callback_url

    if extra_data is not None:
        # CyberSource allows us to send additional data in "merchant defined data" fields
        for num, item in enumerate(extra_data, start=1):
            key = u"merchant_defined_data{num}".format(num=num)
            params[key] = item

    return params


def get_purchase_endpoint():
    """
    Return the URL of the payment end-point for CyberSource.

    Returns:
        unicode

    """
    return get_processor_config().get('PURCHASE_ENDPOINT', '')


def _payment_accepted(order_id, auth_amount, currency, decision):
    """
    Check that CyberSource has accepted the payment.

    Args:
        order_num (int): The ID of the order associated with this payment.
        auth_amount (Decimal): The amount the user paid using CyberSource.
        currency (str): The currency code of the payment.
        decision (str): "ACCEPT" if the payment was accepted.

    Returns:
        dictionary of the form:
        {
            'accepted': bool,
            'amnt_charged': int,
            'currency': string,
            'order': Order
        }

    Raises:
        CCProcessorDataException: The order does not exist.
        CCProcessorWrongAmountException: The user did not pay the correct amount.

    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise CCProcessorDataException(_("The payment processor accepted an order whose number is not in our system."))

    if decision == 'ACCEPT':
        if auth_amount == order.total_cost and currency == order.currency:
            return {
                'accepted': True,
                'amt_charged': auth_amount,
                'currency': currency,
                'order': order
            }
        else:
            ex = CCProcessorWrongAmountException(
                _(
                    u"The amount charged by the processor {charged_amount} {charged_amount_currency} is different "
                    u"than the total cost of the order {total_cost} {total_cost_currency}."
                ).format(
                    charged_amount=auth_amount,
                    charged_amount_currency=currency,
                    total_cost=order.total_cost,
                    total_cost_currency=order.currency
                )
            )

            #pylint: disable=attribute-defined-outside-init
            ex.order = order
            raise ex
    else:
        return {
            'accepted': False,
            'amt_charged': 0,
            'currency': 'usd',
            'order': order
        }


def _record_purchase(params, order):
    """
    Record the purchase and run purchased_callbacks

    Args:
        params (dict): The parameters we received from CyberSource.
        order (Order): The order associated with this payment.

    Returns:
        None

    """
    # Usually, the credit card number will have the form "xxxxxxxx1234"
    # Parse the string to retrieve the digits.
    # If we can't find any digits, use placeholder values instead.
    ccnum_str = params.get('req_card_number', '')
    mm = re.search("\d", ccnum_str)
    if mm:
        ccnum = ccnum_str[mm.start():]
    else:
        ccnum = "####"

    if settings.FEATURES.get("LOG_POSTPAY_CALLBACKS"):
        log.info(
            "Order %d purchased with params: %s", order.id, json.dumps(params)
        )

    # Mark the order as purchased and store the billing information
    order.purchase(
        first=params.get('req_bill_to_forename', ''),
        last=params.get('req_bill_to_surname', ''),
        street1=params.get('req_bill_to_address_line1', ''),
        street2=params.get('req_bill_to_address_line2', ''),
        city=params.get('req_bill_to_address_city', ''),
        state=params.get('req_bill_to_address_state', ''),
        country=params.get('req_bill_to_address_country', ''),
        postalcode=params.get('req_bill_to_address_postal_code', ''),
        ccnum=ccnum,
        cardtype=CARDTYPE_MAP[params.get('req_card_type', '')],
        processor_reply_dump=json.dumps(params)
    )


def _record_payment_info(params, order):
    """
    Record the purchase and run purchased_callbacks

    Args:
        params (dict): The parameters we received from CyberSource.

    Returns:
        None
    """
    if settings.FEATURES.get("LOG_POSTPAY_CALLBACKS"):
        log.info(
            "Order %d processed (but not completed) with params: %s", order.id, json.dumps(params)
        )

    order.processor_reply_dump = json.dumps(params)
    order.save()


def _get_processor_decline_html(params):
    """
    Return HTML indicating that the user's payment was declined.

    Args:
        params (dict): Parameters we received from CyberSource.

    Returns:
        unicode: The rendered HTML.

    """
    payment_support_email = microsite.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL)
    return _format_error_html(
        _(
            "Sorry! Our payment processor did not accept your payment.  "
            "The decision they returned was {decision}, "
            "and the reason was {reason}.  "
            "You were not charged. Please try a different form of payment.  "
            "Contact us with payment-related questions at {email}."
        ).format(
            decision='<span class="decision">{decision}</span>'.format(decision=params['decision']),
            reason='<span class="reason">{reason_code}:{reason_msg}</span>'.format(
                reason_code=params['reason_code'],
                reason_msg=REASONCODE_MAP.get(params['reason_code'])
            ),
            email=payment_support_email
        )
    )


def _get_processor_exception_html(exception):
    """
    Return HTML indicating that an error occurred.

    Args:
        exception (CCProcessorException): The exception that occurred.

    Returns:
        unicode: The rendered HTML.

    """
    payment_support_email = microsite.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL)
    if isinstance(exception, CCProcessorDataException):
        return _format_error_html(
            _(
                u"Sorry! Our payment processor sent us back a payment confirmation that had inconsistent data! "
                u"We apologize that we cannot verify whether the charge went through and take further action on your order. "
                u"The specific error message is: {msg} "
                u"Your credit card may possibly have been charged.  Contact us with payment-specific questions at {email}."
            ).format(
                msg=u'<span class="exception_msg">{msg}</span>'.format(msg=exception.message),
                email=payment_support_email
            )
        )
    elif isinstance(exception, CCProcessorWrongAmountException):
        return _format_error_html(
            _(
                u"Sorry! Due to an error your purchase was charged for a different amount than the order total! "
                u"The specific error message is: {msg}. "
                u"Your credit card has probably been charged. Contact us with payment-specific questions at {email}."
            ).format(
                msg=u'<span class="exception_msg">{msg}</span>'.format(msg=exception.message),
                email=payment_support_email
            )
        )
    elif isinstance(exception, CCProcessorSignatureException):
        return _format_error_html(
            _(
                u"Sorry! Our payment processor sent us back a corrupted message regarding your charge, so we are "
                u"unable to validate that the message actually came from the payment processor. "
                u"The specific error message is: {msg}. "
                u"We apologize that we cannot verify whether the charge went through and take further action on your order. "
                u"Your credit card may possibly have been charged. Contact us with payment-specific questions at {email}."
            ).format(
                msg=u'<span class="exception_msg">{msg}</span>'.format(msg=exception.message),
                email=payment_support_email
            )
        )
    elif isinstance(exception, CCProcessorUserCancelled):
        return _format_error_html(
            _(
                u"Sorry! Our payment processor sent us back a message saying that you have cancelled this transaction. "
                u"The items in your shopping cart will exist for future purchase. "
                u"If you feel that this is in error, please contact us with payment-specific questions at {email}."
            ).format(
                email=payment_support_email
            )
        )
    elif isinstance(exception, CCProcessorUserDeclined):
        return _format_error_html(
            _(
                u"We're sorry, but this payment was declined. The items in your shopping cart have been saved. "
                u"If you have any questions about this transaction, please contact us at {email}."
            ).format(
                email=payment_support_email
            )
        )
    else:
        return _format_error_html(
            _(
                u"Sorry! Your payment could not be processed because an unexpected exception occurred. "
                u"Please contact us at {email} for assistance."
            ).format(email=payment_support_email)
        )


def _format_error_html(msg):
    """ Format an HTML error message """
    return u'<p class="error_msg">{msg}</p>'.format(msg=msg)


CARDTYPE_MAP = defaultdict(lambda: "UNKNOWN")
CARDTYPE_MAP.update(
    {
        '001': 'Visa',
        '002': 'MasterCard',
        '003': 'American Express',
        '004': 'Discover',
        '005': 'Diners Club',
        '006': 'Carte Blanche',
        '007': 'JCB',
        '014': 'EnRoute',
        '021': 'JAL',
        '024': 'Maestro',
        '031': 'Delta',
        '033': 'Visa Electron',
        '034': 'Dankort',
        '035': 'Laser',
        '036': 'Carte Bleue',
        '037': 'Carta Si',
        '042': 'Maestro Int.',
        '043': 'GE Money UK card'
    }
)


# Note: these messages come directly from official Cybersource documentation at:
# http://apps.cybersource.com/library/documentation/dev_guides/CC_Svcs_SO_API/html/wwhelp/wwhimpl/js/html/wwhelp.htm#href=reason_codes.html
REASONCODE_MAP = defaultdict(lambda: DEFAULT_REASON)
REASONCODE_MAP.update(
    {
        '100': _('Successful transaction.'),
        '101': _('The request is missing one or more required fields.'),
        '102': _('One or more fields in the request contains invalid data.'),
        '104': dedent(_(
            """
            The merchant reference code for this authorization request matches the merchant reference code of another
            authorization request that you sent within the past 15 minutes.
            Possible action: Resend the request with a unique merchant reference code.
            """)),
        '110': _('Only a partial amount was approved.'),
        '150': _('General system failure.'),
        '151': dedent(_(
            """
            The request was received but there was a server timeout. This error does not include timeouts between the
            client and the server.
            """)),
        '152': _('The request was received, but a service did not finish running in time.'),
        '200': dedent(_(
            """
            The authorization request was approved by the issuing bank but declined by CyberSource
            because it did not pass the Address Verification System (AVS).
            """)),
        '201': dedent(_(
            """
            The issuing bank has questions about the request. You do not receive an
            authorization code programmatically, but you might receive one verbally by calling the processor.
            Possible action: retry with another form of payment.
            """)),
        '202': dedent(_(
            """
            Expired card. You might also receive this if the expiration date you
            provided does not match the date the issuing bank has on file.
            Possible action: retry with another form of payment.
            """)),
        '203': dedent(_(
            """
            General decline of the card. No other information provided by the issuing bank.
            Possible action: retry with another form of payment.
            """)),
        '204': _('Insufficient funds in the account. Possible action: retry with another form of payment.'),
        # 205 was Stolen or lost card.  Might as well not show this message to the person using such a card.
        '205': _('Stolen or lost card.'),
        '207': _('Issuing bank unavailable. Possible action: retry again after a few minutes.'),
        '208': dedent(_(
            """
            Inactive card or card not authorized for card-not-present transactions.
            Possible action: retry with another form of payment.
            """)),
        '209': _('CVN did not match.'),
        '210': _('The card has reached the credit limit. Possible action: retry with another form of payment.'),
        '211': _('Invalid card verification number (CVN). Possible action: retry with another form of payment.'),
        # 221 was The customer matched an entry on the processor's negative file.
        # Might as well not show this message to the person using such a card.
        '221': _('The customer matched an entry on the processors negative file.'),
        '222': _('Account frozen. Possible action: retry with another form of payment.'),
        '230': dedent(_(
            """
            The authorization request was approved by the issuing bank but declined by
            CyberSource because it did not pass the CVN check.
            Possible action: retry with another form of payment.
            """)),
        '231': _('Invalid account number. Possible action: retry with another form of payment.'),
        '232': dedent(_(
            """
            The card type is not accepted by the payment processor.
            Possible action: retry with another form of payment.
            """)),
        '233': _('General decline by the processor.  Possible action: retry with another form of payment.'),
        '234': _(
            "There is a problem with the information in your CyberSource account.  Please let us know at {0}"
        ).format(settings.PAYMENT_SUPPORT_EMAIL),
        '235': _('The requested capture amount exceeds the originally authorized amount.'),
        '236': _('Processor Failure.  Possible action: retry the payment'),
        '237': _('The authorization has already been reversed.'),
        '238': _('The authorization has already been captured.'),
        '239': _('The requested transaction amount must match the previous transaction amount.'),
        '240': dedent(_(
            """
            The card type sent is invalid or does not correlate with the credit card number.
            Possible action: retry with the same card or another form of payment.
            """)),
        '241': _('The request ID is invalid.'),
        '242': dedent(_(
            """
            You requested a capture, but there is no corresponding, unused authorization record. Occurs if there was
            not a previously successful authorization request or if the previously successful authorization has already
            been used by another capture request.
            """)),
        '243': _('The transaction has already been settled or reversed.'),
        '246': dedent(_(
            """
            Either the capture or credit is not voidable because the capture or credit information has already been
            submitted to your processor, or you requested a void for a type of transaction that cannot be voided.
            """)),
        '247': _('You requested a credit for a capture that was previously voided.'),
        '250': _('The request was received, but there was a timeout at the payment processor.'),
        '254': _('Stand-alone credits are not allowed.'),
        '475': _('The cardholder is enrolled for payer authentication'),
        '476': _('Payer authentication could not be authenticated'),
        '520': dedent(_(
            """
            The authorization request was approved by the issuing bank but declined by CyberSource based
            on your legacy Smart Authorization settings.
            Possible action: retry with a different form of payment.
            """)),
    }
)


def is_user_payment_error(reason_code):
    """
    Decide, based on the reason_code, whether or not it signifies a problem
    with something the user did (rather than a system error beyond the user's
    control).

    This function is used to determine whether we can/should show the user a
    message with suggested actions to fix the problem, or simply apologize and
    ask her to try again later.
    """
    reason_code = str(reason_code)
    if reason_code not in REASONCODE_MAP or REASONCODE_MAP[reason_code] == DEFAULT_REASON:
        return False

    return (200 <= int(reason_code) <= 233) or int(reason_code) in (101, 102, 240)
