"""
Middleware to override CSP headers.
"""

import re

from django.conf import settings


def _load_headers(override=None) -> dict:
    """
    Return a dict of headers to append to every response, based on settings.
    """
    # .. setting_name: CSP_STATIC_ENFORCE
    # .. setting_default: None
    # .. setting_description: Content-Security-Policy header to attach to all responses.
    #   This should include everything but the ``report-to`` or ``report-uri`` clauses; those
    #   will be appended automatically according to the ``CSP_STATIC_REPORTING_NAME`` and
    #   ``CSP_STATIC_REPORTING_URI`` settings. Newlines are permitted and will be replaced with spaces.
    #   A trailing `;` is also permitted.
    # .. setting_warning: Setting the CSP header to too strict a value can cause your pages to
    #   break. It is strongly recommended that deployers start by using ``CSP_STATIC_REPORT_ONLY`` (along
    #   with the reporting settings) and only move or copy the policies into ``CSP_STATIC_ENFORCE`` after
    #   confirming that the received CSP reports only represent false positives. (The report-only
    #   and enforcement headers may be used at the same time.)
    enforce_policies = override or getattr(settings, 'CSP_STATIC_ENFORCE', None)

    # .. setting_name: CSP_STATIC_REPORT_ONLY
    # .. setting_default: None
    # .. setting_description: Content-Security-Policy-Report-Only header to attach to
    #   all responses. See ``CSP_STATIC_ENFORCE`` for details.
    report_policies = getattr(settings, 'CSP_STATIC_REPORT_ONLY', None)

    # .. setting_name: CSP_STATIC_REPORTING_URI
    # .. setting_default: None
    # .. setting_description: URL of reporting server. This will be used for both Level 2 and
    #   Level 3 reports. If there are any semicolons or commas in the URL, they must be URL-encoded.
    #   Level 3 reporting is only enabled if ``CSP_STATIC_REPORTING_NAME`` is also set.
    reporting_uri = getattr(settings, 'CSP_STATIC_REPORTING_URI', None)

    # .. setting_name: CSP_STATIC_REPORTING_NAME
    # .. setting_default: None
    # .. setting_description: Used for CSP Level 3 reporting. This sets the name to use in the
    #   report-to CSP field and the Reporting-Endpoints header. If omitted, then Level 3 CSP
    #   reporting will not be enabled. If present, this must be a string starting with an ASCII
    #   letter and can contain ASCII letters, numbers, hyphen, underscore, and some other characters.
    #   See https://www.rfc-editor.org/rfc/rfc8941.html#section-3.3.4 for full grammar.
    reporting_endpoint_name = getattr(settings, 'CSP_STATIC_REPORTING_NAME', None)

    if not enforce_policies and not report_policies:
        return {}

    headers = {}

    reporting_suffix = ''
    if reporting_uri:
        reporting_suffix = f"; report-uri {reporting_uri}"
        if reporting_endpoint_name:
            headers['Reporting-Endpoints'] = f'{reporting_endpoint_name}="{reporting_uri}"'
            reporting_suffix += f"; report-to {reporting_endpoint_name}"

    def clean_header(value):
        # Collapse any internal whitespace that contains a newline. This allows
        # writing the setting value as a multi-line string, which is useful for
        # CSP -- the values can be quite long.
        value = re.sub("\\s*\n\\s*", " ", value).strip()
        # Remove any trailing semicolon, which we allow (for convenience).
        # The CSP spec does not allow trailing semicolons or empty directives.
        value = re.sub("[;\\s]+$", "", value)
        return value

    if enforce_policies:
        headers['Content-Security-Policy'] = clean_header(enforce_policies) + reporting_suffix

    if report_policies:
        headers['Content-Security-Policy-Report-Only'] = clean_header(report_policies) + reporting_suffix

    return headers


def _append_headers(response_headers, more_headers):
    """
    Append to the response headers. If a header already exists, assume it is
    permitted to be multi-valued (comma-separated), and update the existing value.

    Arguments:
        response_headers: response.headers (or any dict-like object), to be modified
        more_headers: Dict of header names to values
    """
    for k, v in more_headers.items():
        if existing := response_headers.get(k):
            response_headers[k] = f"{existing}, {v}"
        else:
            response_headers[k] = v


class MiddlewareNotUsed(Exception):
    """This middleware is not used in this server configuration"""


def _get_override(request, url_specific_csps):
    """
    Check the CUSTOM_CSPS environment variable for a match to the request url.
    If a regex is included that matches the request url, that means that the CSP header
    should be overwritten with the provided string for this url.
    """
    if not url_specific_csps or not isinstance(url_specific_csps, list):
        return None
    # TODO: handle errors for when env variable has wrong format
    for csp in url_specific_csps:
        if not isinstance(csp, list) or len(csp) != 2:
            continue
        regex, custom_csp = csp
        if re.search(regex, request.path):
            return custom_csp
    return None


def content_security_policy_middleware(get_response):
    """
    Return middleware handler based on CSP headers.
    These are specified in the environment variables `CSP_STATIC_ENFORCE`,
    `CSP_STATIC_REPORT_ONLY`, `CSP_STATIC_REPORTING_URI`, and `CSP_STATIC_REPORTING_NAME`.

    It is possible to override the CSP headers for specific URLs by setting the
    `CUSTOM_CSPS` environment variable to a list of tuples. Each tuple should
    contain a regex and a string. If the regex matches the request URL, the
    CSP header part specified in `CSP_STATIC_ENFORCE` will be overwritten with the provided string.
    """
    csp_headers = _load_headers()
    get_csp_override = getattr(settings, 'GET_CUSTOM_CSPS', None)
    url_specific_csps = get_csp_override() if get_csp_override else None
    # import pdb; pdb.set_trace()
    if not csp_headers and not url_specific_csps:
        raise MiddlewareNotUsed()  # tell Django to skip this middleware

    def middleware_handler(request):
        response = get_response(request)
        # Reporting-Endpoints, CSP, and CSP-RO can all be multi-valued
        # (comma-separated) headers, though the CSP spec says "SHOULD NOT"
        # for the latter two.
        override = _get_override(request, url_specific_csps)

        csp_headers = _load_headers(override=override)
        if csp_headers:
            _append_headers(response.headers, csp_headers)
        return response

    return middleware_handler
