from django.conf import settings
from xmodule.open_ended_grading_classes import peer_grading_service
from .staff_grading_service import StaffGradingService
from xmodule.open_ended_grading_classes.controller_query_service import ControllerQueryService
import json
from student.models import unique_id_for_user
from courseware.models import StudentModule
import logging
from courseware.access import has_access
from util.cache import cache
import datetime
from xmodule.x_module import ModuleSystem
from mitxmako.shortcuts import render_to_string
import datetime

from xblock.field_data import DictFieldData

log = logging.getLogger(__name__)

NOTIFICATION_CACHE_TIME = 300
KEY_PREFIX = "open_ended_"

NOTIFICATION_TYPES = (
    ('student_needs_to_peer_grade', 'peer_grading', 'Peer Grading'),
    ('staff_needs_to_grade', 'staff_grading', 'Staff Grading'),
    ('new_student_grading_to_view', 'open_ended_problems', 'Problems you have submitted'),
    ('flagged_submissions_exist', 'open_ended_flagged_problems', 'Flagged Submissions')
)


def staff_grading_notifications(course, user):
    staff_gs = StaffGradingService(settings.OPEN_ENDED_GRADING_INTERFACE)
    pending_grading = False
    img_path = ""
    course_id = course.id
    student_id = unique_id_for_user(user)
    notification_type = "staff"

    success, notification_dict = get_value_from_cache(student_id, course_id, notification_type)
    if success:
        return notification_dict

    try:
        notifications = json.loads(staff_gs.get_notifications(course_id))
        if notifications['success']:
            if notifications['staff_needs_to_grade']:
                pending_grading = True
    except:
        #Non catastrophic error, so no real action
        notifications = {}
        #This is a dev_facing_error
        log.info(
            "Problem with getting notifications from staff grading service for course {0} user {1}.".format(course_id,
                                                                                                            student_id))

    if pending_grading:
        img_path = "/static/images/grading_notification.png"

    notification_dict = {'pending_grading': pending_grading, 'img_path': img_path, 'response': notifications}

    set_value_in_cache(student_id, course_id, notification_type, notification_dict)

    return notification_dict


def peer_grading_notifications(course, user):
    system = ModuleSystem(
        ajax_url=None,
        track_function=None,
        get_module = None,
        render_template=render_to_string,
        replace_urls=None,
        xmodule_field_data=DictFieldData({}),
    )
    peer_gs = peer_grading_service.PeerGradingService(settings.OPEN_ENDED_GRADING_INTERFACE, system)
    pending_grading = False
    img_path = ""
    course_id = course.id
    student_id = unique_id_for_user(user)
    notification_type = "peer"

    success, notification_dict = get_value_from_cache(student_id, course_id, notification_type)
    if success:
        return notification_dict

    try:
        notifications = json.loads(peer_gs.get_notifications(course_id, student_id))
        if notifications['success']:
            if notifications['student_needs_to_peer_grade']:
                pending_grading = True
    except:
        #Non catastrophic error, so no real action
        notifications = {}
        #This is a dev_facing_error
        log.info(
            "Problem with getting notifications from peer grading service for course {0} user {1}.".format(course_id,
                                                                                                           student_id))
    if pending_grading:
        img_path = "/static/images/grading_notification.png"

    notification_dict = {'pending_grading': pending_grading, 'img_path': img_path, 'response': notifications}

    set_value_in_cache(student_id, course_id, notification_type, notification_dict)

    return notification_dict


def combined_notifications(course, user):
    """
    Show notifications to a given user for a given course.  Get notifications from the cache if possible,
    or from the grading controller server if not.
    @param course: The course object for which we are getting notifications
    @param user: The user object for which we are getting notifications
    @return: A dictionary with boolean pending_grading (true if there is pending grading), img_path (for notification
    image), and response (actual response from grading controller server).
    """
    #Set up return values so that we can return them for error cases
    pending_grading = False
    img_path = ""
    notifications={}
    notification_dict = {'pending_grading': pending_grading, 'img_path': img_path, 'response': notifications}

    #We don't want to show anonymous users anything.
    if not user.is_authenticated():
        return notification_dict

    #Define a mock modulesystem
    system = ModuleSystem(
        static_url="/static",
        ajax_url=None,
        track_function=None,
        get_module = None,
        render_template=render_to_string,
        replace_urls=None,
        xmodule_field_data=DictFieldData({})
    )
    #Initialize controller query service using our mock system
    controller_qs = ControllerQueryService(settings.OPEN_ENDED_GRADING_INTERFACE, system)
    student_id = unique_id_for_user(user)
    user_is_staff = has_access(user, course, 'staff')
    course_id = course.id
    notification_type = "combined"

    #See if we have a stored value in the cache
    success, notification_dict = get_value_from_cache(student_id, course_id, notification_type)
    if success:
        return notification_dict

    #Get the time of the last login of the user
    last_login = user.last_login
    last_time_viewed = last_login - datetime.timedelta(seconds=(NOTIFICATION_CACHE_TIME + 60))

    try:
        #Get the notifications from the grading controller
        controller_response = controller_qs.check_combined_notifications(course.id, student_id, user_is_staff,
                                                                         last_time_viewed)
        notifications = json.loads(controller_response)
        if notifications.get('success'):
            if (notifications.get('staff_needs_to_grade') or
                notifications.get('student_needs_to_peer_grade')):
                pending_grading = True
    except:
        #Non catastrophic error, so no real action
        #This is a dev_facing_error
        log.exception(
            "Problem with getting notifications from controller query service for course {0} user {1}.".format(
                course_id, student_id))

    if pending_grading:
        img_path = "/static/images/grading_notification.png"

    notification_dict = {'pending_grading': pending_grading, 'img_path': img_path, 'response': notifications}

    #Store the notifications in the cache
    set_value_in_cache(student_id, course_id, notification_type, notification_dict)

    return notification_dict


def get_value_from_cache(student_id, course_id, notification_type):
    key_name = create_key_name(student_id, course_id, notification_type)
    success, value = _get_value_from_cache(key_name)
    return success, value


def set_value_in_cache(student_id, course_id, notification_type, value):
    key_name = create_key_name(student_id, course_id, notification_type)
    _set_value_in_cache(key_name, value)


def create_key_name(student_id, course_id, notification_type):
    key_name = "{prefix}{type}_{course}_{student}".format(prefix=KEY_PREFIX, type=notification_type, course=course_id,
                                                          student=student_id)
    return key_name


def _get_value_from_cache(key_name):
    value = cache.get(key_name)
    success = False
    if value is None:
        return success, value
    try:
        value = json.loads(value)
        success = True
    except:
        pass
    return success, value


def _set_value_in_cache(key_name, value):
    cache.set(key_name, json.dumps(value), NOTIFICATION_CACHE_TIME)
