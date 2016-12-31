"""
Views related to the LTI Passport feature.
"""
import json
import requests
import logging

from requests.exceptions import RequestException
from xmodule.modulestore.django import modulestore
from edxmako.shortcuts import render_to_response  # pylint: disable=import-error

from django.conf import settings
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponseBadRequest, Http404
from django.utils.safestring import mark_safe

from labster_course_license.utils import LtiPassport, course_tree_info, SimulationValidationError
from labster_course_license.models import CourseLicense
from ccx_keys.locator import CCXLocator
from ccx.views import coach_dashboard, get_ccx_for_coach
from ccx.overrides import get_override_for_ccx, override_field_for_ccx, clear_override_for_ccx


log = logging.getLogger(__name__)


class ItemNotFoundError(Exception):
    """
    This exception is raised in the case where items is not found in Labster API.
    """
    pass


class LabsterApiError(Exception):
    """
    This exception is raised in the case where problems with Labster API appear.
    """
    pass


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@coach_dashboard
def license_handler(request, course, ccx=None):
    """
    Labster License handler.
    """
    if request.method == 'GET':
        return dashboard(request, course, ccx)
    elif request.method == 'POST':
        return set_license(request, course, ccx)
    return HttpResponseBadRequest('Only GET and POST methods are supported.')


def dashboard(request, course, ccx):
    """
    Display the Course License Dashboard.
    """
    # right now, we can only have one ccx per user and course
    # so, if no ccx is passed in, we can sefely redirect to that
    if ccx is None:
        ccx = get_ccx_for_coach(course, request.user)

    context = {
        'course': course,
        'ccx': ccx,
    }

    if ccx:
        ccx_locator = CCXLocator.from_course_locator(course.id, ccx.id)
        context['license'] = CourseLicense.get_license(ccx_locator)
        context['labster_license_url'] = reverse('labster_license_handler', kwargs={'course_id': ccx_locator})
    else:
        context['ccx_coach_dashboard'] = reverse('ccx_coach_dashboard', kwargs={'course_id': course.id})
    return render_to_response('labster/course_license.html', context)


def apply_field_overrides(ccx, course_info, descriptors):
    """
    Applies field overrides for the given descriptors.
    """
    field_name = 'visible_to_staff_only'
    for descriptor in descriptors:
        info = course_info[descriptor]
        if info.is_hidden:
            override_field_for_ccx(ccx, descriptor, field_name, info.is_hidden)
        else:
            # In case, when the block should be visible field overrides are removed
            # to get most actual values from Master course.
            # It fixes the issue when the block is hidden in Master Course, but is still
            # displayed in CCX that causes Permission Denied error for end users.
            clear_override_for_ccx(ccx, descriptor, field_name)
        apply_field_overrides(ccx, course_info, info.children)


def _send_request(url, data):
    """
    Sends a request the Labster API.
    """
    headers = {
        "authorization": 'Token {}'.format(settings.LABSTER_API_AUTH_TOKEN),
        "content-type": 'application/json',
        "accept": 'application/json',
    }
    response = None

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except RequestException as ex:
        if getattr(response, 'status_code', None) == 404:
            raise ItemNotFoundError
        else:
            log.exception("Labster API is unavailable:\n%r", ex)
            raise LabsterApiError(_("Labster API is unavailable."))
    except ValueError as ex:
        log.error("Invalid JSON:\n%r", ex)
        raise LabsterApiError(_("Invalid JSON."))


def get_consumer_secret(user, license):
    """
    Return consumer and secret keys.
    Raises: LabsterApiError
    """
    data = {
        'user_email': user.email,
        'license': license,
        'source': 'EDX',
    }
    url = settings.LABSTER_ENDPOINTS.get('consumer_secret')
    response = _send_request(url, data)
    return response['consumer_key'], response['secret_key']


def get_licensed_simulations(consumer_keys):
    """
    Return a list of available for the user simulation ids.
    Raises: LabsterApiError
    """
    data = {'consumer_keys': consumer_keys}
    url = settings.LABSTER_ENDPOINTS.get('available_simulations')
    response = _send_request(url, data)
    return set(response)


def passport_by_lti_id(passports, expected_lti_id):
    """
    Return an index of the passport with specified `lti_id(str)`.
    """
    for index, passport_str in enumerate(passports):
        passport = LtiPassport(passport_str)
        if passport.lti_id == expected_lti_id:
            return passport, index
    return None, None


def set_license(request, course, ccx):
    """
    Set lti passport for the CCX.
    """
    if not ccx:
        raise Http404

    course_key = course.location.course_key
    ccx_locator = CCXLocator.from_course_locator(course.id, ccx.id)
    url = reverse('labster_license_handler', kwargs={'course_id': ccx_locator})

    # Getting consumer and secret keys.
    license = request.POST.get('license', None)
    if not license:
        messages.error(request, _('Please set your license. The field cannot be empty.'))
        return redirect(url)

    try:
        consumer_key, secret_key = get_consumer_secret(request.user, license)
    except LabsterApiError as api_err:
        messages.error(
            request, _('There are some issues with applying your license. Please try again in a few minutes.')
        )
        log.error("Unable to get consumer secret for license {}: {}".format(license, api_err))
        return redirect(url)
    except ItemNotFoundError:
        messages.error(request, _('Ensure you are using correct License code.'))
        return redirect(url)

    # Update passports
    passports = get_override_for_ccx(ccx, course, 'lti_passports', course.lti_passports)[:]
    passport, index = passport_by_lti_id(passports, settings.LABSTER_DEFAULT_LTI_ID)

    if passport:
        passport.consumer_key = consumer_key
        passport.secret_key = secret_key
        passports[index] = str(passport)
    else:
        passport = LtiPassport.construct(settings.LABSTER_DEFAULT_LTI_ID, consumer_key, secret_key)
        passports.append(str(passport))

    override_field_for_ccx(ccx, course, 'lti_passports', passports)
    CourseLicense.set_license(ccx_locator, license)

    update_course_structure = request.POST.get('update', None)
    if not update_course_structure:
        return redirect(url)

    try:
        update_course(ccx, course_key, passports)
    except (LabsterApiError, ItemNotFoundError):
        messages.error(
            request, _('Your license is successfully applied, but there was an error with updating your course.')
        )
        return redirect(url)
    except SimulationValidationError as err:
        msg = _((
            'Please verify LTI URLs are correct for the following simulations:<br><br> {}'
        ).format(
            '<br><br>'.join(
                'Simulation name is "{}"<br>Simulation id is "{}"<br>Error message: <b>{}</b>'.format(
                    sim_name, sim_id, err_msg
                ) for sim_name, sim_id, err_msg in err.message
            )
        ))
        messages.error(request, mark_safe(msg))
        return redirect(url)

    url = reverse('labster_license_handler', kwargs={'course_id': CCXLocator.from_course_locator(course.id, ccx.id)})
    return redirect(url)


def update_course(ccx, course_key, passports):
    """
    Updates the course to show/hide blocks depends on the available simulations.
    """
    # Getting a list of licensed simulations
    consumer_keys = [LtiPassport(passport_str).consumer_key for passport_str in passports]
    # Updating the course: hides unlicensed simulations.
    licensed_simulations = get_licensed_simulations(consumer_keys)
    store = modulestore()
    with store.bulk_operations(course_key):
        lti_blocks = store.get_items(course_key, qualifiers={'category': 'lti'})
        # Filter a list of lti blocks to get only blocks with simulations.
        simulations = (block for block in lti_blocks if '/simulation/' in block.launch_url)
        course_info, chapters = course_tree_info(store, simulations, licensed_simulations)
        apply_field_overrides(ccx, course_info, chapters)
