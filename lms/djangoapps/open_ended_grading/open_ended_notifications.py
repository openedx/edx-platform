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

log=logging.getLogger(__name__)

NOTIFICATION_TYPES = (
    ('student_needs_to_peer_grade', 'peer_grading', 'Peer Grading'),
    ('staff_needs_to_grade', 'staff_grading', 'Staff Grading'),
    ('overall_need_to_check', 'open_ended_problems', 'Problems you have submitted')
    )

def staff_grading_notifications(course):
    staff_gs = StaffGradingService(settings.STAFF_GRADING_INTERFACE)
    pending_grading=False
    img_path= ""
    course_id = course.id
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

    return {'pending_grading' : pending_grading, 'img_path' : img_path, 'response' : notifications}

def peer_grading_notifications(course, user):
    peer_gs = PeerGradingService(settings.PEER_GRADING_INTERFACE)
    pending_grading=False
    img_path= ""
    course_id = course.id

    try:
        notifications = json.loads(peer_gs.get_notifications(course_id,unique_id_for_user(user)))
        if notifications['success']:
            if notifications['student_needs_to_peer_grade']:
                pending_grading=True
    except:
        #Non catastrophic error, so no real action
        notifications = {}
        log.info("Problem with getting notifications from peer grading service.")

    if pending_grading:
        img_path = "/static/images/slider-handle.png"

    return {'pending_grading' : pending_grading, 'img_path' : img_path, 'response' : notifications}

def combined_notifications(course, user):
    controller_url = open_ended_util.get_controller_url()
    controller_qs = ControllerQueryService(controller_url)
    student_id = unique_id_for_user(user)
    user_is_staff = has_access(user, course, 'staff')
    course_id = course.id

    min_time_to_query = user.last_login
    last_module_seen = StudentModule.objects.filter(student=user, course_id = course_id, modified__gt=min_time_to_query).values('modified').order_by('-modified')
    last_module_seen_count = last_module_seen.count()

    if last_module_seen_count>0:
        last_time_viewed = last_module_seen[0]['modified']
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

    return {'pending_grading' : pending_grading, 'img_path' : img_path, 'response' : notifications}