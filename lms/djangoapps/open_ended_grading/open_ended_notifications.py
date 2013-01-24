from django.conf import settings
from staff_grading_service import StaffGradingService
from peer_grading_service import PeerGradingService
from open_ended_grading.controller_query_service import ControllerQueryService
import json
from student.models import unique_id_for_user
import open_ended_util
from courseware.models import StudentModule
import logging
from courseware.access import has_access
from util.cache import cache
import datetime

log=logging.getLogger(__name__)

NOTIFICATION_CACHE_TIME = 300
KEY_PREFIX = "open_ended_"

NOTIFICATION_TYPES = (
    ('student_needs_to_peer_grade', 'peer_grading', 'Peer Grading'),
    ('staff_needs_to_grade', 'staff_grading', 'Staff Grading'),
    ('new_student_grading_to_view', 'open_ended_problems', 'Problems you have submitted')
    )

def staff_grading_notifications(course, user):
    staff_gs = StaffGradingService(settings.STAFF_GRADING_INTERFACE)
    pending_grading=False
    img_path= ""
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
                pending_grading=True
    except:
        #Non catastrophic error, so no real action
        notifications = {}
        log.info("Problem with getting notifications from staff grading service.")

    if pending_grading:
        img_path = "/static/images/slider-handle.png"

    notification_dict = {'pending_grading' : pending_grading, 'img_path' : img_path, 'response' : notifications}

    set_value_in_cache(student_id, course_id, notification_type, notification_dict)

    return notification_dict

def peer_grading_notifications(course, user):
    peer_gs = PeerGradingService(settings.PEER_GRADING_INTERFACE)
    pending_grading=False
    img_path= ""
    course_id = course.id
    student_id = unique_id_for_user(user)
    notification_type = "peer"

    success, notification_dict = get_value_from_cache(student_id, course_id, notification_type)
    if success:
        return notification_dict

    try:
        notifications = json.loads(peer_gs.get_notifications(course_id,student_id))
        if notifications['success']:
            if notifications['student_needs_to_peer_grade']:
                pending_grading=True
    except:
        #Non catastrophic error, so no real action
        notifications = {}
        log.info("Problem with getting notifications from peer grading service.")

    if pending_grading:
        img_path = "/static/images/slider-handle.png"

    notification_dict = {'pending_grading' : pending_grading, 'img_path' : img_path, 'response' : notifications}

    set_value_in_cache(student_id, course_id, notification_type, notification_dict)

    return notification_dict

def combined_notifications(course, user):
    controller_url = open_ended_util.get_controller_url()
    controller_qs = ControllerQueryService(controller_url)
    student_id = unique_id_for_user(user)
    user_is_staff = has_access(user, course, 'staff')
    course_id = course.id
    notification_type = "combined"

    success, notification_dict = get_value_from_cache(student_id, course_id, notification_type)
    if success:
        return notification_dict

    min_time_to_query = user.last_login
    last_module_seen = StudentModule.objects.filter(student=user, course_id = course_id, modified__gt=min_time_to_query).values('modified').order_by('-modified')
    last_module_seen_count = last_module_seen.count()

    if last_module_seen_count>0:
        last_time_viewed = last_module_seen[0]['modified'] - datetime.timedelta(seconds=(NOTIFICATION_CACHE_TIME + 60))
    else:
        last_time_viewed = user.last_login

    pending_grading= False

    img_path= ""
    try:
        controller_response = controller_qs.check_combined_notifications(course.id,student_id, user_is_staff, last_time_viewed)
        log.debug(controller_response)
        notifications = json.loads(controller_response)
        if notifications['success']:
            if notifications['overall_need_to_check']:
                pending_grading=True
    except:
        #Non catastrophic error, so no real action
        notifications = {}
        log.exception("Problem with getting notifications from controller query service.")

    if pending_grading:
        img_path = "/static/images/slider-handle.png"

    notification_dict = {'pending_grading' : pending_grading, 'img_path' : img_path, 'response' : notifications}

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
    key_name = "{prefix}{type}_{course}_{student}".format(prefix=KEY_PREFIX, type=notification_type, course=course_id, student=student_id)
    return key_name

def _get_value_from_cache(key_name):
    value = cache.get(key_name)
    success = False
    if value is None:
        return success , value
    try:
        value = json.loads(value)
        success = True
    except:
        pass
    return success , value

def _set_value_in_cache(key_name, value):
    cache.set(key_name, json.dumps(value), NOTIFICATION_CACHE_TIME)