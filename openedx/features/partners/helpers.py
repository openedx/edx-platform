import pytz

from datetime import datetime
from importlib import import_module
from logging import getLogger

from django.http import Http404

from course_action_state.models import CourseRerunState
from custom_settings.models import CustomSettings
from nodebb.tasks import task_join_group_on_nodebb
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.features.course_card.helpers import get_course_open_date, get_related_card_id
from openedx.features.course_card.models import CourseCard
from student.models import CourseEnrollment

log = getLogger(__name__)

PARTNERS_VIEW_FRMT = 'openedx.features.partners.{slug}.views'


def get_partner_recommended_courses(partner_slug, user):
    """
    get recommend courses those are tagged with partner's slug
    :param partner_slug: slug of partner with which courses are tagged
    :return: list of recommended courses
    """
    recommended_courses = []
    current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)

    partner_course_settings = CustomSettings.objects.filter(tags__icontains=partner_slug).all()

    # Make a set of card id's to remove duplication
    partner_course_card_ids = {get_related_card_id(crs_setting.id) for crs_setting in partner_course_settings}

    for course_id in partner_course_card_ids:
        course_reruns = [crs.course_key for crs in CourseRerunState.objects.filter(
            source_course_key=course_id, action="rerun", state="succeeded")]
        course_rerun_states = course_reruns + [course_id]

        if not course_reruns:
            try:
                CourseCard.objects.get(course_id=course_id)
            except CourseCard.DoesNotExist:
                # This is a parent course and it's card isn't added
                continue

        course_rerun_object = CourseOverview.objects.select_related('image_set').filter(
            id__in=course_rerun_states, enrollment_start__lte=current_time, enrollment_end__gte=current_time
        ).order_by('start').first()

        if course_rerun_object:
            course_rerun_object.start = get_course_open_date(course_rerun_object)
            course_rerun_object.description = get_course_description(course_rerun_object)
            course_rerun_object.enrolled = CourseEnrollment.is_enrolled(user, course_rerun_object.id)
            recommended_courses.append(course_rerun_object)

    return recommended_courses


def get_course_description(course):
    """
    This function returns the description of the course added via cms
    :param course:
    :return: description
    """
    description = ""
    try:
        description = CourseDetails.fetch_about_attribute(course.id, 'description')
    except Exception as ex:
        pass
    return description


def import_module_using_slug(partner_slug):
    try:
        return import_module(PARTNERS_VIEW_FRMT.format(slug=partner_slug))
    except ImportError:
        raise Http404('Your partner is not properly registered')


def auto_join_partner_community(partner, user):
    community_ids = partner.communities.all().values_list('community_id', flat=True)
    username = user.username
    for community_id in community_ids:
        task_join_group_on_nodebb.delay(category_id=community_id, username=username)
        log.info('Task to auto join user {username} in community '
                 'with id {community_id} for partner {slug} is added to celery'
                 .format(community_id=community_id, username=username, slug=partner.slug))
