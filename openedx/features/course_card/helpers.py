from course_action_state.models import CourseRerunState


def get_related_card_id(course_id):
    """
    Get course key from parent course
    :param course_id:
    :return:
    """
    course_rerun = CourseRerunState.objects.filter(course_key=course_id).first()
    if course_rerun:
        return course_rerun.source_course_key

    return course_id


def is_course_rereun(course_id):
    """
    Check if the course is created as rerun
    :param course_id:
    :return:
    """
    course_rerun = CourseRerunState.objects.filter(course_key=course_id).first()
    if course_rerun:
        return course_rerun.source_course_key

    return None
