import datetime
from django.conf import settings

from oef.models import OefSurvey, TopicQuestion, OptionLevel, OrganizationOefScore, Instruction
from oef.messages import NON_APPLICABLE_OEF, PENDING_DRAFT


def get_user_survey_status(user, create_new_survey=True):
    """
    This function determines, whether a user is
    eligible to take a new oef survey. If a user
    has a pending survey, return that to user
    if user took a survey less that days limit
    specified in setting, return none
    """
    error = ''
    is_eligible = True
    survey = None
    uos = None
    try:
        uos = OrganizationOefScore.objects.filter(user=user).latest('start_date')
    except OrganizationOefScore.DoesNotExist:
        pass

    if not uos:
        if create_new_survey:
            survey = OefSurvey.objects.filter(is_enabled=True).latest('created')

        return {
            'error': error,
            'is_eligible': is_eligible,
            'survey': survey
        }

    if not uos.finish_date:
        error = PENDING_DRAFT
        is_eligible = False
        survey = OefSurvey.objects.filter(is_enabled=True).latest('created')
    else:
        limit = settings.OEF_RENEWAL_DAYS
        if (datetime.date.today() - uos.modified.date()).days < limit:
            is_eligible = False
            error = NON_APPLICABLE_OEF
        elif create_new_survey:
            survey = OefSurvey.objects.filter(is_enabled=True).latest('created')

    return {
        'error': error,
        'is_eligible': is_eligible,
        'survey': survey
    }


def get_user_survey(user, latest_survey):
    """
    Create/Get a user-survey object, if one
    in pending already exists, return that
    """
    uos = None
    try:
        uos = OrganizationOefScore.objects.filter(user_id=user.id).filter(finish_date__isnull=True).latest('start_date')
    except OrganizationOefScore.DoesNotExist:
        pass

    if not uos:
        uos = OrganizationOefScore()
        uos.user = user
        uos.org = user.extended_profile.organization
        uos.start_date = datetime.date.today()
        uos.save()

    return uos


def get_survey_topics(uos, survey_id):
    topics = TopicQuestion.objects.filter(survey_id=survey_id).order_by("order_number")
    parsed_topics = []
    for index, topic in enumerate(topics):
        options = topic.options.order_by('level__value')
        answer = getattr(uos, topic.score_name)
        parsed_topics.append({
            'title': topic.title,
            'description': topic.description,
            'index': index + 1,
            'id': topic.id,
            'score_name': topic.score_name,
            'options': options,
            'answer': answer
        })
    return parsed_topics


def get_option_levels():
    return OptionLevel.objects.order_by('value')


def get_oef_instructions():
    return Instruction.objects.filter(is_enabled=True).order_by('question_index')


def get_option(option_value):
    return OptionLevel.objects.get(value=option_value)
