import datetime

from django.conf import settings

from lms.djangoapps.oef.models import OefSurvey, TopicQuestion, UserOefSurvey, UserAnswers, OptionLevel, Instruction
from lms.djangoapps.oef.messages import NON_APPLICABLE_OEF, PENDING_DRAFT


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
        uos = UserOefSurvey.objects.filter(user=user).latest('started_on')
    except UserOefSurvey.DoesNotExist:
        pass

    if not uos:
        if create_new_survey:
            survey = OefSurvey.objects.filter(is_enabled=True).latest('created')

        return {
            'error': error,
            'is_eligible': is_eligible,
            'survey': survey
        }

    if uos.status == 'pending':
        error = PENDING_DRAFT
        is_eligible = False
        survey = uos.survey
    else:
        limit = settings.OEF_RENEWAL_DAYS
        if (datetime.date.today() - uos.started_on).days < limit:
            is_eligible = False
            error = NON_APPLICABLE_OEF % limit
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
        uos = UserOefSurvey.objects.get(user_id=user.id, status='pending')
    except UserOefSurvey.DoesNotExist:
        pass

    if not uos:
        uos = UserOefSurvey()
        uos.survey = latest_survey
        uos.user = user
        uos.survey_date = datetime.date.today()
        uos.started_on = datetime.date.today()
        uos.save()

    return uos


def is_answered(uos, question_id):
    return UserAnswers.objects.filter(user_survey_id=uos.id).filter(question_id=question_id).exists()


def get_survey_topics(uos, survey_id):
    topics = TopicQuestion.objects.filter(survey_id=survey_id).order_by("order_number")
    parsed_topics = []
    for index, topic in enumerate(topics):
        options = topic.options.order_by('level__value')
        # options.sort(key=lambda x: x.level.value, reverse=False)
        answer = get_answer(uos, topic.id)
        parsed_topics.append({
            'title': topic.title,
            'description': topic.description,
            'index': index + 1,
            'id': topic.id,
            'options': options,
            'answer': answer.selected_option.value if answer else None
        })
    return parsed_topics


def get_option_levels():
    return OptionLevel.objects.order_by('value')

def get_oef_instructions():
    return Instruction.objects.filter(is_enabled=True).order_by('question_index')


def get_answer(uos, question_id):
    try:
        return UserAnswers.objects.get(user_survey_id=uos.id, question_id=question_id)
    except UserAnswers.DoesNotExist:
        return None


def create_answer(uos, data):
    return UserAnswers(user_survey=uos, question_id=int(data['topic_id']))


def get_option(option_value):
    return OptionLevel.objects.get(value=option_value)


def check_if_complete(uos, answers_count):
    """
    Check if the survey has been completed
    if yes, mark it complete
    """
    if uos.survey.topics.count() == answers_count:
        uos.status = 'completed'
        uos.completed_on = datetime.date.today()
        uos.save()
