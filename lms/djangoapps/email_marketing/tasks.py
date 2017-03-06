"""
This file contains celery tasks for email marketing signal handler.
"""
import logging
import time

from celery import task
from django.contrib.auth.models import User
from django.http import Http404
from django.core.cache import cache

from email_marketing.models import EmailMarketingConfiguration
from course_modes.models import CourseMode
from courseware.courses import get_course_by_id
from student.models import EnrollStatusChange

from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)


# pylint: disable=not-callable
@task(bind=True, default_retry_delay=3600, max_retries=24)
def update_user(self, username, new_user=False, activation=False):
    """
    Adds/updates Sailthru profile information for a user.
     Args:
        username(str): A string representation of user identifier
    Returns:
        None
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # get user
    try:
        user = User.objects.select_related('profile').get(username=username)
    except User.DoesNotExist:
        log.error("User not found during Sailthru update %s", username)
        return

    # get profile
    profile = user.profile

    sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
    try:
        sailthru_response = sailthru_client.api_post("user",
                                                     _create_sailthru_user_parm(user, profile, new_user, email_config))
    except SailthruClientError as exc:
        log.error("Exception attempting to add/update user %s in Sailthru - %s", username, unicode(exc))
        raise self.retry(exc=exc,
                         countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        # put out error and schedule retry
        log.error("Error attempting to add/update user in Sailthru: %s", error.get_message())
        raise self.retry(countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)

    # if activating user, send welcome email
    if activation and email_config.sailthru_activation_template:
        try:
            sailthru_response = sailthru_client.api_post("send",
                                                         {"email": user.email,
                                                          "template": email_config.sailthru_activation_template})
        except SailthruClientError as exc:
            log.error("Exception attempting to send welcome email to user %s in Sailthru - %s", username, unicode(exc))
            raise self.retry(exc=exc,
                             countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)

        if not sailthru_response.is_ok():
            error = sailthru_response.get_error()
            # probably an invalid template name, just put out error
            log.error("Error attempting to send welcome email to user in Sailthru: %s", error.get_message())


# pylint: disable=not-callable
@task(bind=True, default_retry_delay=3600, max_retries=24)
def update_user_email(self, username, old_email):
    """
    Adds/updates Sailthru when a user email address is changed
     Args:
        username(str): A string representation of user identifier
        old_email(str): Original email address
    Returns:
        None
    """
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    # get user
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        log.error("User not found duing Sailthru update %s", username)
        return

    # ignore if email not changed
    if user.email == old_email:
        return

    sailthru_parms = {"id": old_email, "key": "email", "keysconflict": "merge", "keys": {"email": user.email}}

    try:
        sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)
        sailthru_response = sailthru_client.api_post("user", sailthru_parms)
    except SailthruClientError as exc:
        log.error("Exception attempting to update email for %s in Sailthru - %s", username, unicode(exc))
        raise self.retry(exc=exc,
                         countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)

    if not sailthru_response.is_ok():
        error = sailthru_response.get_error()
        log.error("Error attempting to update user email address in Sailthru: %s", error.get_message())
        raise self.retry(countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)


def _create_sailthru_user_parm(user, profile, new_user, email_config):
    """
    Create sailthru user create/update parms from user + profile.
    """
    sailthru_user = {'id': user.email, 'key': 'email'}
    sailthru_vars = {'username': user.username,
                     'activated': int(user.is_active),
                     'joined_date': user.date_joined.strftime("%Y-%m-%d")}
    sailthru_user['vars'] = sailthru_vars
    sailthru_vars['last_changed_time'] = int(time.time())

    if profile:
        sailthru_vars['fullname'] = profile.name
        sailthru_vars['gender'] = profile.gender
        sailthru_vars['education'] = profile.level_of_education
        # age is not useful since it is not automatically updated
        #sailthru_vars['age'] = profile.age or -1
        if profile.year_of_birth:
            sailthru_vars['year_of_birth'] = profile.year_of_birth
        sailthru_vars['country'] = unicode(profile.country.code)

    # if new user add to list
    if new_user and email_config.sailthru_new_user_list:
        sailthru_user['lists'] = {email_config.sailthru_new_user_list: 1}

    return sailthru_user


# pylint: disable=not-callable
@task(bind=True, default_retry_delay=3600, max_retries=24)
def update_course_enrollment(self, email, course_url, event, mode,
                             unit_cost=None, course_id=None,
                             currency=None, message_id=None):  # pylint: disable=unused-argument
    """
    Adds/updates Sailthru when a user enrolls/unenrolls/adds to cart/purchases/upgrades a course
     Args:
        email(str): The user's email address
        course_url(str): Course home page url
        event(str): event type
        mode(object): enroll mode (audit, verification, ...)
        unit_cost: cost if purchase event
        course_id(CourseKey): course id
        currency(str): currency if purchase event - currently ignored since Sailthru only supports USD
    Returns:
        None


    The event can be one of the following:
        EnrollStatusChange.enroll
            A free enroll (mode=audit)
        EnrollStatusChange.unenroll
            An unenroll
        EnrollStatusChange.upgrade_start
            A paid upgrade added to cart
        EnrollStatusChange.upgrade_complete
            A paid upgrade purchase complete
        EnrollStatusChange.paid_start
            A non-free course added to cart
        EnrollStatusChange.paid_complete
            A non-free course purchase complete
    """

    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    course_id_string = course_id.to_deprecated_string()

    # Use event type to figure out processing required
    new_enroll = unenroll = fetch_tags = False
    incomplete = send_template = None
    if unit_cost:
        cost_in_cents = unit_cost * 100

    if event == EnrollStatusChange.enroll:
        # new enroll for audit (no cost)
        new_enroll = True
        fetch_tags = True
        send_template = email_config.sailthru_enroll_template
        # set cost of $1 so that Sailthru recognizes the event
        cost_in_cents = email_config.sailthru_enroll_cost

    elif event == EnrollStatusChange.unenroll:
        # unenroll - need to update list of unenrolled courses for user in Sailthru
        unenroll = True

    elif event == EnrollStatusChange.upgrade_start:
        # add upgrade to cart
        incomplete = 1

    elif event == EnrollStatusChange.paid_start:
        # add course purchase (probably 'honor') to cart
        incomplete = 1

    elif event == EnrollStatusChange.upgrade_complete:
        # upgrade complete
        fetch_tags = True
        send_template = email_config.sailthru_upgrade_template

    elif event == EnrollStatusChange.paid_complete:
        # paid course purchase complete
        new_enroll = True
        fetch_tags = True
        send_template = email_config.sailthru_purchase_template

    sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)

    # update the "unenrolled" course array in the user record on Sailthru if new enroll or unenroll
    if new_enroll or unenroll:
        if not _update_unenrolled_list(sailthru_client, email, course_url, unenroll):
            raise self.retry(countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)

    # if there is a cost, call Sailthru purchase api to record
    if cost_in_cents:

        # get course information if configured and appropriate event
        if fetch_tags and email_config.sailthru_get_tags_from_sailthru:
            course_data = _get_course_content(course_url, sailthru_client, email_config)
        else:
            course_data = {}

        # build item description
        item = _build_purchase_item(course_id_string, course_url, cost_in_cents, mode, course_data, course_id)

        # build purchase api options list
        options = {}
        if incomplete and email_config.sailthru_abandoned_cart_template:
            options['reminder_template'] = email_config.sailthru_abandoned_cart_template
            options['reminder_time'] = "+{} minutes".format(email_config.sailthru_abandoned_cart_delay)

        # add appropriate send template
        if send_template:
            options['send_template'] = send_template

        if not _record_purchase(sailthru_client, email, item, incomplete, message_id, options):
            raise self.retry(countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)


def _build_purchase_item(course_id_string, course_url, cost_in_cents, mode, course_data, course_id):
    """
    Build Sailthru purchase item object
    :return: item
    """

    # build item description
    item = {
        'id': "{}-{}".format(course_id_string, mode),
        'url': course_url,
        'price': cost_in_cents,
        'qty': 1,
    }

    # get title from course info if we don't already have it from Sailthru
    if 'title' in course_data:
        item['title'] = course_data['title']
    else:
        try:
            course = get_course_by_id(course_id)
            item['title'] = course.display_name
        except Http404:
            # can't find, just invent title
            item['title'] = 'Course {} mode: {}'.format(course_id_string, mode)

    if 'tags' in course_data:
        item['tags'] = course_data['tags']

    # add vars to item
    sailthru_vars = {}
    if 'vars' in course_data:
        sailthru_vars = course_data['vars']
    sailthru_vars['mode'] = mode
    sailthru_vars['course_run_id'] = course_id_string
    item['vars'] = sailthru_vars

    # get list of modes for course and add upgrade deadlines for verified modes
    for mode_entry in CourseMode.modes_for_course(course_id):
        if mode_entry.expiration_datetime is not None and CourseMode.is_verified_slug(mode_entry.slug):
            sailthru_vars['upgrade_deadline_{}'.format(mode_entry.slug)] = \
                mode_entry.expiration_datetime.strftime("%Y-%m-%d")

    return item


def _record_purchase(sailthru_client, email, item, incomplete, message_id, options):
    """
    Record a purchase in Sailthru
    :param sailthru_client:
    :param email:
    :param item:
    :param incomplete:
    :param message_id:
    :param options:
    :return: False it retryable error
    """
    try:
        sailthru_response = sailthru_client.purchase(email, [item],
                                                     incomplete=incomplete, message_id=message_id,
                                                     options=options)

        if not sailthru_response.is_ok():
            error = sailthru_response.get_error()
            log.error("Error attempting to record purchase in Sailthru: %s", error.get_message())
            return False

    except SailthruClientError as exc:
        log.error("Exception attempting to record purchase for %s in Sailthru - %s", email, unicode(exc))
        return False

    return True


def _get_course_content(course_url, sailthru_client, email_config):
    """
    Get course information using the Sailthru content api.

    If there is an error, just return with an empty response.
    :param course_url:
    :param sailthru_client:
    :return: dict with course information
    """
    # check cache first
    response = cache.get(course_url)
    if not response:
        try:
            sailthru_response = sailthru_client.api_get("content", {"id": course_url})

            if not sailthru_response.is_ok():
                return {}

            response = sailthru_response.json
            cache.set(course_url, response, email_config.sailthru_content_cache_age)

        except SailthruClientError:
            response = {}

    return response


def _update_unenrolled_list(sailthru_client, email, course_url, unenroll):
    """
    Maintain a list of courses the user has unenrolled from in the Sailthru user record
    :param sailthru_client:
    :param email:
    :param email_config:
    :param course_url:
    :param unenroll:
    :return: False if retryable error, else True
    """
    try:
        # get the user 'vars' values from sailthru
        sailthru_response = sailthru_client.api_get("user", {"id": email, "fields": {"vars": 1}})
        if not sailthru_response.is_ok():
            error = sailthru_response.get_error()
            log.error("Error attempting to read user record from Sailthru: %s", error.get_message())
            return False

        response_json = sailthru_response.json

        unenroll_list = []
        if response_json and "vars" in response_json and "unenrolled" in response_json["vars"]:
            unenroll_list = response_json["vars"]["unenrolled"]

        changed = False
        # if unenrolling, add course to unenroll list
        if unenroll:
            if course_url not in unenroll_list:
                unenroll_list.append(course_url)
                changed = True

        # if enrolling, remove course from unenroll list
        elif course_url in unenroll_list:
            unenroll_list.remove(course_url)
            changed = True

        if changed:
            # write user record back
            sailthru_response = sailthru_client.api_post(
                "user", {'id': email, 'key': 'email', "vars": {"unenrolled": unenroll_list}})

            if not sailthru_response.is_ok():
                error = sailthru_response.get_error()
                log.error("Error attempting to update user record in Sailthru: %s", error.get_message())
                return False

        # everything worked
        return True

    except SailthruClientError as exc:
        log.error("Exception attempting to update user record for %s in Sailthru - %s", email, unicode(exc))
        return False
