from django.conf import settings
from staff_grading_service import StaffGradingService
from peer_grading_service import PeerGradingService
from open_ended_grading.controller_query_service import ControllerQueryService
import json
from student.models import unique_id_for_user
import open_ended_util
from courseware.models import StudentModule

def staff_grading_notifications(course):
    staff_gs = StaffGradingService(settings.STAFF_GRADING_INTERFACE)
    pending_grading=False
    img_path= ""
    try:
        notifications = json.loads(staff_gs.get_notifications(course.id))
        if notifications['success']:
            if notifications['staff_needs_to_grade']:
                pending_grading=True
    except:
        #Non catastrophic error, so no real action
        log.info("Problem with getting notifications from staff grading service.")

    if pending_grading:
        img_path = "/static/images/slider-handle.png"

    return {'pending_grading' : pending_grading, 'img_path' : img_path, 'response' : notifications}

def peer_grading_notifications(course, user):
    peer_gs = PeerGradingService(settings.PEER_GRADING_INTERFACE)
    pending_grading=False
    img_path= ""
    try:
        notifications = json.loads(peer_gs.get_notifications(course.id,unique_id_for_user(user)))
        if notifications['success']:
            if notifications['student_needs_to_peer_grade']:
                pending_grading=True
    except:
        #Non catastrophic error, so no real action
        log.info("Problem with getting notifications from peer grading service.")

    if pending_grading:
        img_path = "/static/images/slider-handle.png"

    return {'pending_grading' : pending_grading, 'img_path' : img_path, 'response' : notifications}

def combined_notifications(course, user):
    controller_url = open_ended_util.get_controller_url()
    controller_qs = ControllerQueryService(controller_url)
    student_id = unique_id_for_user(user)
    course_id = course.id
    user_is_staff  = has_access(user, course, 'staff')

    min_time_to_query = user.last_login
    last_module_seen = StudentModule.objects.all(student=user, course_id = course_id, modified__gt=min_time_to_query).values('modified').order_by('-modified')[0]

    last_time_viewed = last_module_seen['modified']
    pending_grading= False

    img_path= ""
    try:
        notifications = json.loads(controller_qs.get_notifications(course.id,student_id, user_is_staff, last_time_viewed))
        if notifications['success']:
            if notifications['overall_need_to_check']:
                pending_grading=True
    except:
        #Non catastrophic error, so no real action
        log.info("Problem with getting notifications from controller query service.")

    if pending_grading:
        img_path = "/static/images/slider-handle.png"

    return {'pending_grading' : pending_grading, 'img_path' : img_path, 'response' : notifications}