"""
Views for Survey
"""
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from survey.models import SurveySubmission
from util.json_request import JsonResponse


log = logging.getLogger(__name__)


@require_POST
@login_required
@ensure_csrf_cookie
def survey_init(request):
    """Returns whether the survey has already submitted."""
    course_id = request.POST.get('course_id')
    unit_id = request.POST.get('unit_id')

    if not course_id or not unit_id:
        log.warning("Illegal parameter. course_id=%s, unit_id=%s" % (course_id, unit_id))
        raise Http404

    try:
        submission = SurveySubmission.objects.filter(
            course_id=course_id,
            unit_id=unit_id,
            user=request.user
        ).order_by('created')[0:1].get()
    except SurveySubmission.DoesNotExist:
        pass
    else:
        return JsonResponse({
            'success': False,
            'survey_answer': submission.get_survey_answer(),
        })

    return JsonResponse({'success': True})


@require_POST
@login_required
@ensure_csrf_cookie
def survey_ajax(request):
    """Ajax call to submit a survey."""
    MAX_CHARACTER_LENGTH = 1000

    course_id = request.POST.get('course_id')
    unit_id = request.POST.get('unit_id')
    survey_name = request.POST.get('survey_name')
    survey_answer = request.POST.get('survey_answer')

    if not course_id or not unit_id:
        log.warning("Illegal parameter. course_id=%s, unit_id=%s" % (course_id, unit_id))
        raise Http404
    if not survey_name:
        log.warning("Illegal parameter. survey_name=%s" % survey_name)
        raise Http404
    if not survey_answer:
        log.warning("Illegal parameter. survey_answer=%s" % survey_answer)
        raise Http404
    try:
        obj = json.loads(survey_answer)
    except:
        log.warning("Illegal parameter. survey_answer=%s" % survey_answer)
        raise Http404
    for k, v in obj.iteritems():
        if len(v) > MAX_CHARACTER_LENGTH:
            log.warning("%s cannot be more than %d characters long." % (k, MAX_CHARACTER_LENGTH))
            raise Http404

    try:
        submission = SurveySubmission.objects.filter(
            course_id=course_id,
            unit_id=unit_id,
            user=request.user
        ).order_by('created')[0:1].get()
    except SurveySubmission.DoesNotExist:
        pass
    else:
        return JsonResponse({
            'success': False,
            'survey_answer': submission.get_survey_answer(),
        })

    submission = SurveySubmission(
        course_id=course_id,
        unit_id=unit_id,
        user=request.user,
        survey_name=survey_name,
        survey_answer=survey_answer,
    )
    submission.save()
    return JsonResponse({'success': True})
