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
import requests
import csv
import StringIO
import pytz
from textwrap import dedent
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from django.conf import settings
from django.utils.translation import ugettext as _
from edxmako.shortcuts import render_to_string
from shoppingcart.models import (
    Order,
    PaymentTransaction,
    TRANSACTION_TYPE_PURCHASE,
    TRANSACTION_TYPE_REFUND,
    PaymentTransactionSyncError
)
from shoppingcart.processors.exceptions import *
from shoppingcart.processors.helpers import get_processor_config
from microsite_configuration import microsite

log = logging.getLogger(__name__)


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

REASONCODE_MAP = defaultdict(lambda: "UNKNOWN REASON")
REASONCODE_MAP.update(
    {
        '100': _('Successful transaction.'),
        '102': _('One or more fields in the request contains invalid data.'),
        '104': dedent(_(
            """
            The access_key and transaction_uuid fields for this authorization request matches the access_key and
            transaction_uuid of another authorization request that you sent in the last 15 minutes.
            Possible fix: retry the payment after 15 minutes.
            """)),
        '110': _('Only a partial amount was approved.'),
        '200': dedent(_(
            """
            The authorization request was approved by the issuing bank but declined by CyberSource
            because it did not pass the Address Verification System (AVS).
            """)),
        '201': dedent(_(
            """
            The issuing bank has questions about the request. You do not receive an
            authorization code programmatically, but you might receive one verbally by calling the processor.
            Possible fix: retry with another form of payment
            """)),
        '202': dedent(_(
            """
            Expired card. You might also receive this if the expiration date you
            provided does not match the date the issuing bank has on file.
            Possible fix: retry with another form of payment
            """)),
        '203': dedent(_(
            """
            General decline of the card. No other information provided by the issuing bank.
            Possible fix: retry with another form of payment
            """)),
        '204': _('Insufficient funds in the account. Possible fix: retry with another form of payment'),
        # 205 was Stolen or lost card.  Might as well not show this message to the person using such a card.
        '205': _('Stolen or lost card'),
        '207': _('Issuing bank unavailable. Possible fix: retry again after a few minutes'),
        '208': dedent(_(
            """
            Inactive card or card not authorized for card-not-present transactions.
            Possible fix: retry with another form of payment
            """)),
        '210': _('The card has reached the credit limit. Possible fix: retry with another form of payment'),
        '211': _('Invalid card verification number (CVN). Possible fix: retry with another form of payment'),
        # 221 was The customer matched an entry on the processor's negative file.
        # Might as well not show this message to the person using such a card.
        '221': _('The customer matched an entry on the processors negative file.'),
        '222': _('Account frozen. Possible fix: retry with another form of payment'),
        '230': dedent(_(
            """
            The authorization request was approved by the issuing bank but declined by
            CyberSource because it did not pass the CVN check.
            Possible fix: retry with another form of payment
            """)),
        '231': _('Invalid account number. Possible fix: retry with another form of payment'),
        '232': dedent(_(
            """
            The card type is not accepted by the payment processor.
            Possible fix: retry with another form of payment
            """)),
        '233': _('General decline by the processor.  Possible fix: retry with another form of payment'),
        '234': _(
            "There is a problem with the information in your CyberSource account.  Please let us know at {0}"
        ).format(settings.PAYMENT_SUPPORT_EMAIL),
        '236': _('Processor Failure.  Possible fix: retry the payment'),
        '240': dedent(_(
            """
            The card type sent is invalid or does not correlate with the credit card number.
            Possible fix: retry with the same card or another form of payment
            """)),
        '475': _('The cardholder is enrolled for payer authentication'),
        '476': _('Payer authentication could not be authenticated'),
        '520': dedent(_(
            """
            The authorization request was approved by the issuing bank but declined by CyberSource based
            on your legacy Smart Authorization settings.
            Possible fix: retry with a different form of payment.
            """)),
    }
)


def synchronize_transactions(start_date, end_date):
    """
    Concrete implementation of the API. This will call out to CyberSource Secure Acceptance
    Batch Processing Detail Report which can be provided on a daily basis
    """

    # truncate the date ranges to midnight
    start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    cur_date = start_date
    num_fetched = 0
    num_processed = 0
    num_in_err = 0
    errs = []

    log.info('Starting transaction synchronization from {start} to {end}'.format(
        start=start_date, end=end_date,
    ))

    # CyberSource only supports getting a report for a single day
    while cur_date < end_date:
        log.info('\nSynchronizing transaction report data for day: {0}'.format(cur_date))
        daily_report = get_report_data(cur_date)
        num_fetched = num_fetched + len(daily_report)
        log.info('Got {num} records'.format(num=num_fetched))

        _num_processed, _num_in_err, _errs = process_report_data(daily_report)
        log.info('{success_num} records successfully processed, {err_num} records failed'.format(
            success_num=_num_processed, err_num=_num_in_err,
        ))
        num_processed = num_processed + _num_processed
        num_in_err = num_in_err + _num_in_err
        errs.extend(_errs)

        # go to next day
        cur_date = cur_date + timedelta(1)

    return num_processed, num_in_err, errs


RECEIVED_REPORT_FIELD_NAMES = [
    'batch_id',
    'merchant_id',
    'batch_date',
    'request_id',
    'merchant_ref_number',
    'trans_ref_no',
    'payment_method',
    'currency',
    'amount',
    'transaction_type',
]


def get_report_data_for_account(account_name, config, date):
    """
    This gets the report data (PaymentBatchDetailReport) for a specified account configuration
    """

    url = "{base_hostname}/DownloadReport/{date_str}/{acct_name}/PaymentBatchDetailReport.csv".format(
        base_hostname=config['REPORTING_BASE_ENDPOINT'],
        date_str=date.strftime('%Y/%m/%d'),
        acct_name=account_name
    )

    log.info('Fetching CyberSource transaction data via: {}'.format(url))

    response = requests.get(url, auth=(config['REPORTING_AUTH_USERNAME'], config['REPORTING_AUTH_PASSWORD']))
    if response.status_code == 400:
        # CyberSource will return 400's if a date is requested that it can't fulfill

        now = datetime.now(pytz.UTC)
        now.replace(hour=0, minute=0, second=0, microsecond=0)  # pylint: disable=maybe-no-member

        # CyberSource will not support downloading of data more than 180 days old
        if now - date >= timedelta(179):
            log.info(
                'CyberSource does not support getting transaction dumps more than '
                '180 days old. Returning empty set.'
            )
            return []

        # Can't ask for things in the future or even today's report
        if date >= now - timedelta(1):
            log.info('Requested date in the future. Returning empty set.')
            return []
    if response.status_code == 403:
        raise CCProcessorFailedSyncronization('HTTP Auth Credentials for Report Services failed or were locked out!')
    elif response.status_code != 200:
        msg = 'PaymentBatchDetailReport failed with status code of {status_code}!'.format(
            status_code=response.status_code
        )
        raise CCProcessorFailedSyncronization(msg)

    # Parse the CSV
    csv_buffer = StringIO.StringIO(response.content)

    reader = csv.DictReader(csv_buffer, fieldnames=RECEIVED_REPORT_FIELD_NAMES)

    # Filter out the keys we aren't including in the output
    # Remove the first two rows, which are just header info
    data = [
        {
            key: val
            for key, val in row.iteritems()
        }
        for row in reader
    ][2:]

    return data


def get_report_data(date):
    """
    Internal method to make the remote call to CyberSource Reporting Services to get all transactions for all of
    the CyberSource accounts that are defined in configuration.

    The method returns an arrary of dicts containing all transaction data from CyberSource on that day
    """

    # get the 'root' account information
    account_name = settings.CC_PROCESSOR['CyberSource2'].get('REPORTING_ACCOUNT_NAME')
    if account_name:
        data = get_report_data_for_account(
            account_name,
            settings.CC_PROCESSOR['CyberSource2'],
            date
        )

    # keep track of which accounts we've processed
    processed_accounts = [account_name]

    # now go through all of the various microsites, but don't redo overlapping
    # accounts since multiple microsites might use the same CyberSource account
    for microsite_key in settings.CC_PROCESSOR['CyberSource2'].get('microsites', {}):
        config = settings.CC_PROCESSOR['CyberSource2']['microsites'][microsite_key]
        account_name = config.get('REPORTING_ACCOUNT_NAME')

        if not account_name:
            continue

        if account_name not in processed_accounts:
            _data = get_report_data_for_account(account_name, config, date)
            data.extend(_data)
            processed_accounts.append(account_name)

    return data


def process_report_data(data):
    """
    This function will convert a CyberSource PaymentBatchDetailReport report into our own internal
    ProcessorTransaction tables, as well as note any errors that occured during this processes
    """

    rows_processed = 0
    rows_in_error = 0
    errors = []
    for row in data:
        remote_transaction_id = row['trans_ref_no']
        try:
            account_id = row['merchant_id']
            try:
                processed_at = datetime.strptime(row['batch_date'], '%m/%d/%y')
            except ValueError:
                processed_at = datetime.strptime(row['batch_date'], '%Y-%m-%d')

            processed_at = processed_at.replace(tzinfo=pytz.UTC)
            order_id = int(row['merchant_ref_number'])
            currency = row['currency']
            amount = float(row['amount'])
            _type = row['transaction_type']

            if _type == 'ics_bill':
                transaction_type = TRANSACTION_TYPE_PURCHASE
            elif _type == 'ics_credit':
                transaction_type = TRANSACTION_TYPE_REFUND
            else:
                raise Exception('Unknown transaction_type received: {transaction_type}'.format(transaction_type=_type))

            PaymentTransaction.create(
                remote_transaction_id,
                account_id,
                processed_at,
                order_id,
                currency,
                amount,
                transaction_type
            )
            rows_processed = rows_processed + 1
        except Exception, ex:  # pylint: disable=broad-except
            rows_in_error = rows_in_error + 1
            err = {
                'remote_transaction_id': remote_transaction_id,
                'raw_data': row,
                'err_msg': repr(ex)
            }
            log.error('Failed to process record: {err}'.format(err=err))
            PaymentTransactionSyncError.create_and_save(
                err['remote_transaction_id'],
                err['raw_data'],
                err['err_msg']
            )
            errors.append(err)

    return rows_processed, rows_in_error, errors
