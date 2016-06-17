"""
This file contains celery tasks for email marketing signal handler.
"""
import logging
import time

from celery import task
from django.contrib.auth.models import User

from email_marketing.models import EmailMarketingConfiguration
from student.models import ENROLL_STATUS_CHANGE_ENROLL, \
    ENROLL_STATUS_CHANGE_UNENROLL, \
    ENROLL_STATUS_CHANGE_UPGRADE_ADD_CART, \
    ENROLL_STATUS_CHANGE_UPGRADE_COMPLETE, \
    ENROLL_STATUS_CHANGE_PAID_COURSE_ADD_CART, \
    ENROLL_STATUS_CHANGE_PAID_COURSE_COMPLETE

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
    user = User.objects.select_related('profile').get(username=username)
    if not user:
        log.error("User not found during Sailthru update %s", username)
        return

    # get profile
    profile = user.profile
    if not profile:
        log.error("User profile not found during Sailthru update %s", username)
        return

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
    user = User.objects.get(username=username)
    if not user:
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
                             unit_cost=None, course_id=None, currency=None,
                             message_id=None):
    """
    Adds/updates Sailthru when a user enrolls/unenrolls/adds to cart/purchases/upgrades a course
     Args:
        email(str): The user's email address
        course_url(str): Course home page url
        event(str): event type
        mode(object): enroll mode (audit, verification, ...)
        unit_cost: cost if purchase event
        currency(str): currency if purchase event
    Returns:
        None
    """
    log.info("In update_course_enrollment: course_url=%s, event=%s", course_url, event)
    log.info(mode)
    log.info(unit_cost)
    email_config = EmailMarketingConfiguration.current()
    if not email_config.enabled:
        return

    new_enroll = event == ENROLL_STATUS_CHANGE_ENROLL or event == ENROLL_STATUS_CHANGE_PAID_COURSE_COMPLETE
    unenroll = event == ENROLL_STATUS_CHANGE_UNENROLL
    if event == ENROLL_STATUS_CHANGE_ENROLL:
        unit_cost = 1

    sailthru_client = SailthruClient(email_config.sailthru_key, email_config.sailthru_secret)

    # update the "unenrolled" course array in the user record on Sailthru if new enroll or unenroll
    if new_enroll or unenroll:
        _update_unenrolled_list(self, sailthru_client, email, email_config, course_url, unenroll)

    # if there is a cost, call Sailthru purchase api to record
    if unit_cost:

        # get course information
        course_data = _get_course_content(course_url, sailthru_client)

        # build item description
        item = {'id': course_id + '-' + mode,
                'url': course_url,
                'price': unit_cost * 100,
                'qty': 1,
                }

        if 'title' in course_data:
            item['title'] = course_data['title']
        else:
            item['title'] = 'Course ' + course_id + ' mode: ' + mode

        if 'tags' in course_data:
            item['tags'] = course_data['tags']

        # Mark sale as incomplete if just doing an add cart
        incomplete = None
        if event == ENROLL_STATUS_CHANGE_UPGRADE_ADD_CART or event == ENROLL_STATUS_CHANGE_PAID_COURSE_ADD_CART:
            incomplete = 1

        # build purchase api options list
        options = {}
        if incomplete and email_config.sailthru_abandoned_cart_template:
            options['reminder_template'] = email_config.sailthru_abandoned_cart_template
            options['reminder_time'] = "+{} minutes".format(email_config.sailthru_abandoned_cart_delay)

        # add appropriate send template
        if event == ENROLL_STATUS_CHANGE_ENROLL and email_config.sailthru_enroll_template:
            options['send_template'] = email_config.sailthru_enroll_template
        if event == ENROLL_STATUS_CHANGE_UPGRADE_COMPLETE and email_config.sailthru_upgrade_template:
            options['send_template'] = email_config.sailthru_upgrade_template
        if event == ENROLL_STATUS_CHANGE_PAID_COURSE_COMPLETE and email_config.sailthru_purchase_template:
            options['send_template'] = email_config.sailthru_purchase_template

        # add vars to item
        vars = {}
        if 'vars' in course_data:
            vars = course_data['vars']
        vars['mode'] = mode
        vars['course_run_id'] = course_id
        item['vars'] = vars


        log.info(item)

        try:
            sailthru_response = sailthru_client.purchase(email, [ item ],
                                                         incomplete=incomplete, message_id=message_id,
                                                         options=options)

            if not sailthru_response.is_ok():
                error = sailthru_response.get_error()
                log.error("Error attempting to record purchase in Sailthru: %s", error.get_message())
                raise self.retry(countdown=email_config.sailthru_retry_interval,
                                 max_retries=email_config.sailthru_max_retries)

            response_json = sailthru_response.json
            log.info(response_json)

        except SailthruClientError as exc:
            log.error("Exception attempting to record purchase for %s in Sailthru - %s", email, unicode(exc))
            raise self.retry(exc=exc,
                             countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)


def _get_course_content(course_url, sailthru_client):
    """
    Get course information using the Sailthru content api.

    If there is an error, just return with an empty response.
    :param course_url:
    :param sailthru_client:
    :return: dict with course information
    """
    try:
        sailthru_response = sailthru_client.api_get("content", {"id": course_url})

        if not sailthru_response.is_ok():
            return {}

        response_json = sailthru_response.json
        log.info(response_json)
        return response_json

    except SailthruClientError as exc:
        return {}


def _update_unenrolled_list(self, sailthru_client, email, email_config, course_url, unenroll):
    """
    Maintain a list of courses the user has unenrolled from in the Sailthru user record
    :param sailthru_client:
    :param email:
    :param email_config:
    :param course_url:
    :param unenroll:
    :return:
    """
    try:
        # get the user 'vars' values from sailthru
        sailthru_response = sailthru_client.api_get("user", {"id": email, "fields": {"vars": 1}})
        if not sailthru_response.is_ok():
            error = sailthru_response.get_error()
            log.error("Error attempting to read user record from Sailthru: %s", error.get_message())
            raise self.retry(countdown=email_config.sailthru_retry_interval,
                             max_retries=email_config.sailthru_max_retries)

        response_json = sailthru_response.json
        log.info(response_json)
        unenroll_list = []
        if response_json and "vars" in response_json and "unenrolled" in response_json["vars"]:
            unenroll_list = response_json["vars"]["unenrolled"]

        changed = False
        # if unenrolling, add course to unenroll list
        if unenroll:
            if not course_url in unenroll_list:
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
                raise self.retry(countdown=email_config.sailthru_retry_interval,
                                 max_retries=email_config.sailthru_max_retries)

    except SailthruClientError as exc:
        log.error("Exception attempting to update user record for %s in Sailthru - %s", email, unicode(exc))
        raise self.retry(exc=exc,
                         countdown=email_config.sailthru_retry_interval,
                         max_retries=email_config.sailthru_max_retries)