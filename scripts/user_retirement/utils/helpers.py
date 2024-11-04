"""
Common helper methods to use in user retirement scripts.
"""
# NOTE: Make sure that all non-ascii text written to standard output (including
# print statements and logging) is manually encoded to bytes using a utf-8 or
# other encoding.  We currently make use of this library within a context that
# does NOT tolerate unicode text on sys.stdout, namely python 2 on Build
# Jenkins.  PLAT-2287 tracks this Tech Debt.


import io
import json
import sys
import traceback
import unicodedata

import yaml
from six import text_type

from scripts.user_retirement.utils.edx_api import LmsApi  # pylint: disable=wrong-import-position
from scripts.user_retirement.utils.edx_api import CredentialsApi, EcommerceApi, LicenseManagerApi
from scripts.user_retirement.utils.thirdparty_apis.amplitude_api import \
    AmplitudeApi  # pylint: disable=wrong-import-position
from scripts.user_retirement.utils.thirdparty_apis.braze_api import BrazeApi  # pylint: disable=wrong-import-position
from scripts.user_retirement.utils.thirdparty_apis.hubspot_api import \
    HubspotAPI  # pylint: disable=wrong-import-position
from scripts.user_retirement.utils.thirdparty_apis.salesforce_api import \
    SalesforceApi  # pylint: disable=wrong-import-position
from scripts.user_retirement.utils.thirdparty_apis.segment_api import \
    SegmentApi  # pylint: disable=wrong-import-position


def _log(kind, message):
    """
    Convenience method to log text. Prepended "kind" text makes finding log entries easier.
    """
    print(u'{}: {}'.format(kind, message).encode('utf-8'))  # See note at the top of this file.


def _fail(kind, code, message):
    """
    Convenience method to fail out of the command with a message and traceback.
    """
    _log(kind, message)

    # Try to get a traceback, if there is one. On Python 3.4 this raises an AttributeError
    # if there is no current exception, so we eat that here.
    try:
        _log(kind, traceback.format_exc())
    except AttributeError:
        pass

    sys.exit(code)


def _fail_exception(kind, code, message, exc):
    """
    A version of fail that takes an exception to be utf-8 decoded
    """
    exc_msg = _get_error_str_from_exception(exc)
    message += '\n' + exc_msg
    _fail(kind, code, message)


def _get_error_str_from_exception(exc):
    """
    Return a string from an exception that may or may not have a .content (Slumber)
    """
    exc_msg = text_type(exc)

    if hasattr(exc, 'content'):
        # Slumber inconveniently discards the decoded .text attribute from the Response object,
        # and instead gives us the raw encoded .content attribute, so we need to decode it first.
        # Python 2 needs the decode, Py3 does not have it.
        try:
            exc_msg += '\n' + str(exc.content).decode('utf-8')
        except AttributeError:
            exc_msg += '\n' + str(exc.content)

    return exc_msg


def _config_or_exit(fail_func, fail_code, config_file):
    """
    Returns the config values from the given file, allows overriding of passed in values.
    """
    try:
        with io.open(config_file, 'r') as config:
            config = yaml.safe_load(config)

        return config
    except Exception as exc:  # pylint: disable=broad-except
        fail_func(fail_code, 'Failed to read config file {}'.format(config_file), exc)


def _config_with_drive_or_exit(fail_func, config_fail_code, google_fail_code, config_file, google_secrets_file):
    """
    Returns the config values from the given file, allows overriding of passed in values.
    """
    try:
        with io.open(config_file, 'r') as config:
            config = yaml.safe_load(config)

        # Check required values
        for var in ('org_partner_mapping', 'drive_partners_folder'):
            if var not in config or not config[var]:
                fail_func(config_fail_code, 'No {} in config, or it is empty!'.format(var), ValueError())

        # Force the partner names into NFKC here and when we get the folders to ensure
        # they are using the same characters. Otherwise accented characters will not match.
        for org in config['org_partner_mapping']:
            partner = config['org_partner_mapping'][org]
            config['org_partner_mapping'][org] = [unicodedata.normalize('NFKC', text_type(partner)) for partner in
                                                  config['org_partner_mapping'][org]]
    except Exception as exc:  # pylint: disable=broad-except
        fail_func(config_fail_code, 'Failed to read config file {}'.format(config_file), exc)

    try:
        # Just load and parse the file to make sure it's legit JSON before doing
        # all of the work to get the users.
        with open(google_secrets_file, 'r') as secrets_f:
            json.load(secrets_f)

        config['google_secrets_file'] = google_secrets_file
        return config
    except Exception as exc:  # pylint: disable=broad-except
        fail_func(google_fail_code, 'Failed to read secrets file {}'.format(google_secrets_file), exc)


def _setup_lms_api_or_exit(fail_func, fail_code, config):
    """
    Performs setup of EdxRestClientApi for LMS and returns the validated, sorted list of users to report on.
    """
    try:
        lms_base_url = config['base_urls']['lms']
        client_id = config['client_id']
        client_secret = config['client_secret']

        config['LMS'] = LmsApi(lms_base_url, lms_base_url, client_id, client_secret)
    except Exception as exc:  # pylint: disable=broad-except
        fail_func(fail_code, text_type(exc))


def _setup_all_apis_or_exit(fail_func, fail_code, config):
    """
    Performs setup of EdxRestClientApi instances for LMS, E-Commerce, and Credentials,
    as well as fetching the learner's record from LMS and validating that it is
    in a state to work on. Returns the learner dict and their current stage in
    the retirement flow.
    """
    try:
        lms_base_url = config['base_urls']['lms']
        ecommerce_base_url = config['base_urls'].get('ecommerce', None)
        credentials_base_url = config['base_urls'].get('credentials', None)
        segment_base_url = config['base_urls'].get('segment', None)
        license_manager_base_url = config['base_urls'].get('license_manager', None)
        client_id = config['client_id']
        client_secret = config['client_secret']
        braze_api_key = config.get('braze_api_key', None)
        braze_instance = config.get('braze_instance', None)
        amplitude_api_key = config.get('amplitude_api_key', None)
        amplitude_secret_key = config.get('amplitude_secret_key', None)
        salesforce_user = config.get('salesforce_user', None)
        salesforce_password = config.get('salesforce_password', None)
        salesforce_token = config.get('salesforce_token', None)
        salesforce_domain = config.get('salesforce_domain', None)
        salesforce_assignee = config.get('salesforce_assignee', None)
        segment_auth_token = config.get('segment_auth_token', None)
        segment_workspace_slug = config.get('segment_workspace_slug', None)
        hubspot_api_key = config.get('hubspot_api_key', None)
        hubspot_aws_region = config.get('hubspot_aws_region', None)
        hubspot_from_address = config.get('hubspot_from_address', None)
        hubspot_alert_email = config.get('hubspot_alert_email', None)

        for state in config['retirement_pipeline']:
            for service, service_url in (
                ('BRAZE', braze_api_key),
                ('AMPLITUDE', amplitude_api_key),
                ('ECOMMERCE', ecommerce_base_url),
                ('CREDENTIALS', credentials_base_url),
                ('SEGMENT', segment_base_url),
                ('HUBSPOT', hubspot_api_key),
            ):
                if state[2] == service and service_url is None:
                    fail_func(fail_code, 'Service URL is not configured, but required for state {}'.format(state))

        config['LMS'] = LmsApi(lms_base_url, lms_base_url, client_id, client_secret)

        if braze_api_key:
            config['BRAZE'] = BrazeApi(
                braze_api_key,
                braze_instance,
            )

        if amplitude_api_key and amplitude_secret_key:
            config['AMPLITUDE'] = AmplitudeApi(
                amplitude_api_key,
                amplitude_secret_key,
            )

        if salesforce_user and salesforce_password and salesforce_token:
            config['SALESFORCE'] = SalesforceApi(
                salesforce_user,
                salesforce_password,
                salesforce_token,
                salesforce_domain,
                salesforce_assignee
            )

        if hubspot_api_key:
            config['HUBSPOT'] = HubspotAPI(
                hubspot_api_key,
                hubspot_aws_region,
                hubspot_from_address,
                hubspot_alert_email
            )

        if ecommerce_base_url:
            config['ECOMMERCE'] = EcommerceApi(lms_base_url, ecommerce_base_url, client_id, client_secret)

        if credentials_base_url:
            config['CREDENTIALS'] = CredentialsApi(lms_base_url, credentials_base_url, client_id, client_secret)

        if license_manager_base_url:
            config['LICENSE_MANAGER'] = LicenseManagerApi(
                lms_base_url,
                license_manager_base_url,
                client_id,
                client_secret,
            )

        if segment_base_url:
            config['SEGMENT'] = SegmentApi(
                segment_base_url,
                segment_auth_token,
                segment_workspace_slug
            )
    except Exception as exc:  # pylint: disable=broad-except
        fail_func(fail_code, 'Unexpected error occurred!', exc)
