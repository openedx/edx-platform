import datetime

from django.conf import settings

from lms.djangoapps.oef.models import OefSurvey, TopicQuestion, UserOefSurvey, UserAnswers, OptionLevel


def get_user_survey_status(user, create_new_survey=True):
    error = ''
    is_eligible = True
    survey = None
    try:
        uos = UserOefSurvey.objects.filter(user=user).latest('started_on')
    except UserOefSurvey.DoesNotExist:
        if create_new_survey:
            survey = OefSurvey.objects.filter(is_enabled=True).latest('created')

        return {
            'error': error,
            'is_eligible': is_eligible,
            'survey': survey
        }

    if uos.status == 'pending':
        error = 'You have a pending survey'
        is_eligible = False
        survey = uos.survey
    else:
        limit = settings.OEF_RENEWAL_DAYS
        if (datetime.date.today() - uos.started_on).days < limit:
            is_eligible = False
            error = 'You can request a new OEF survey only after %s days of last survey' % limit
        elif create_new_survey:
            survey = OefSurvey.objects.filter(is_enabled=True).latest('created')

    return {
        'error': error,
        'is_eligible': is_eligible,
        'survey': survey
    }


def get_user_survey(user, latest_survey):
    try:
        uos = UserOefSurvey.objects.get(user_id=user.id, status='in-progress')
    except UserOefSurvey.DoesNotExist:
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
    topics = TopicQuestion.objects.filter(survey_id=survey_id)
    parsed_topics = []
    for index, topic in enumerate(topics):
        options = list(topic.options.all())
        options.sort(key=lambda x: x.level.value, reverse=False)
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
    levels = list(OptionLevel.objects.all())
    levels.sort(key=lambda x: x.value, reverse=False)
    return levels


def get_answer(uos, question_id):
    try:
        return UserAnswers.objects.get(user_survey_id=uos.id, question_id=question_id)
    except UserAnswers.DoesNotExist:
        return None


def create_answer(uos, data):
    answer = UserAnswers()
    answer.user_survey = uos
    answer.question_id = int(data['topic_id'])
    return answer


def get_option(option_value):
    return OptionLevel.objects.get(value=option_value)


def check_if_complete(uos, answers_count):
    if uos.survey.topics.count() == answers_count:
        uos.status = 'completed'
        uos.completed_on = datetime.date.today()
        uos.save()
