# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from newrelic.api.html_insertion import insert_html_snippet
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper
from newrelic.config import extra_settings

from newrelic.packages import six

_logger = logging.getLogger(__name__)

_boolean_states = {
    '1': True, 'yes': True, 'true': True, 'on': True,
    '0': False, 'no': False, 'false': False, 'off': False
}


def _setting_boolean(value):
    if value.lower() not in _boolean_states:
        raise ValueError('Not a boolean: %s' % value)
    return _boolean_states[value.lower()]


_settings_types = {
    'browser_monitoring.auto_instrument': _setting_boolean,
    'browser_monitoring.auto_instrument_passthrough': _setting_boolean,
}

_settings_defaults = {
    'browser_monitoring.auto_instrument': True,
    'browser_monitoring.auto_instrument_passthrough': True,
}

flask_compress_settings = extra_settings('import-hook:flask_compress',
        types=_settings_types, defaults=_settings_defaults)


def _nr_wrapper_Compress_after_request(wrapped, instance, args, kwargs):
    def _params(response, *args, **kwargs):
        return response

    response = _params(*args, **kwargs)

    # Need to be running within a valid web transaction.

    transaction = current_transaction()

    if not transaction:
        return wrapped(*args, **kwargs)

    # Only insert RUM JavaScript headers and footers if enabled
    # in configuration and not already likely inserted.

    if not transaction.settings.browser_monitoring.enabled:
        return wrapped(*args, **kwargs)

    if transaction.autorum_disabled:
        return wrapped(*args, **kwargs)

    if not flask_compress_settings.browser_monitoring.auto_instrument:
        return wrapped(*args, **kwargs)

    if transaction.rum_header_generated:
        return wrapped(*args, **kwargs)

    # Only possible if the content type is one of the allowed
    # values. Normally this is just text/html, but optionally
    # could be defined to be list of further types. For example
    # a user may want to also perform insertion for
    # 'application/xhtml+xml'.

    ctype = (response.mimetype or '').lower()

    if ctype not in transaction.settings.browser_monitoring.content_type:
        return wrapped(*args, **kwargs)

    # Don't risk it if content encoding already set.

    if 'Content-Encoding' in response.headers:
        return wrapped(*args, **kwargs)

    # Don't risk it if content is actually within an attachment.

    cdisposition = response.headers.get('Content-Disposition', '').lower()

    if cdisposition.split(';')[0].strip() == 'attachment':
        return wrapped(*args, **kwargs)

    # No point continuing if header is empty. This can occur if
    # RUM is not enabled within the UI. It is assumed at this
    # point that if header is not empty, then footer will not be
    # empty. We don't want to generate the footer just yet as
    # want to do that as late as possible so that application
    # server time in footer is as accurate as possible. In
    # particular, if the response content is generated on demand
    # then the flattening of the response could take some time
    # and we want to track that. We thus generate footer below
    # at point of insertion.

    header = transaction.browser_timing_header()

    if not header:
        return wrapped(*args, **kwargs)

    # If the response has direct_passthrough flagged, then is
    # likely to be streaming a file or other large response.
    direct_passthrough = getattr(response, 'direct_passthrough', None)
    if direct_passthrough:
        if not (flask_compress_settings.
                browser_monitoring.auto_instrument_passthrough):
            return wrapped(*args, **kwargs)

        # In those cases, if the mimetype is still a supported browser
        # insertion mimetype is not an attachment, and will be compressed, then
        # we should try to go ahead and insert browser stuff since Flask
        # Compress change the response anyway.
        #
        # In order to do that, we have to disable direct_passthrough on the
        # response since we have to immediately read the contents of the file.
        elif ctype == 'text/html':
            response.direct_passthrough = False
        else:
            return wrapped(*args, **kwargs)

    def html_to_be_inserted():
        return six.b(header) + six.b(transaction.browser_timing_footer())

    # Make sure we flatten any content first as it could be
    # stored as a list of strings in the response object. We
    # assign it back to the response object to avoid having
    # multiple copies of the string in memory at the same time
    # as we progress through steps below.

    result = insert_html_snippet(response.get_data(), html_to_be_inserted)

    if result is not None:
        if transaction.settings.debug.log_autorum_middleware:
            _logger.debug('RUM insertion from flask_compress '
                    'triggered. Bytes added was %r.',
                    len(result) - len(response.get_data()))

        response.set_data(result)
        response.headers['Content-Length'] = str(len(response.get_data()))

    return wrapped(*args, **kwargs)


def instrument_flask_compress(module):
    wrap_function_wrapper(module, 'Compress.after_request',
            _nr_wrapper_Compress_after_request)
