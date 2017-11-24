import datetime

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status

from lms.djangoapps.oef.models import OefSurvey, TopicQuestion, UserOefSurvey, UserAnswers


def fetch_survey(request):
    survey = OefSurvey.objects.filter(is_enabled=True).latest('created')
    topics = get_survey_topics(survey.id)
    uos = get_user_survey(request.user, survey)

    return render(request, 'oef/oef_survey.html', {"survey_id": survey.id, "topics": topics})


def get_user_survey(user, survey):
    try:
        uos = UserOefSurvey.objects.get(oef_survey_id=survey.id, user_id=user.id)
    except UserOefSurvey.DoesNotExist:
        uos = UserOefSurvey()
        uos.oef_survey = survey
        uos.user = user
        uos.survey_date = datetime.date.today()
        uos.start_date = datetime.date.today()
        uos.completed_date = datetime.date.today()
        uos.save()

    return uos


def get_survey_topics(survey_id):
    topics = TopicQuestion.objects.filter(survey_id=survey_id)
    parsed_topics = []
    for index, topic in enumerate(topics):
        parsed_topics.append({
            'title': topic.title,
            'index': index + 1,
            'id': topic.id
        })
    return parsed_topics


def get_option_data(option):
    return {
        'text': option.text,
        'priority': option.priority.label,
        'id': option.id
    }


def get_survey_topic(request, topic_id):
    topic_question = TopicQuestion.objects.get(id=topic_id)
    options = topic_question.options.all()
    options = [get_option_data(option) for option in options]
    return JsonResponse({
        'title': topic_question.title,
        'description': topic_question.description,
        'id': topic_question.id,
        'options': options
    }, status=status.HTTP_200_OK)


def get_answer(uos, question_id):
    try:
        return UserAnswers.objects.get(user_survey_id=uos.id, question_id=question_id)
    except UserAnswers.DoesNotExist:
        return None


def create_answer(uos, data):
    answer = UserAnswers()
    answer.user_survey = uos
    answer.question_id = int(data['topic_id'])
    answer.selected_option_id = int(data['answer'])
    answer.save()
    return answer


def save_answer(request):
    data = request.POST
    survey_id = int(data['survey_id'])
    question_id = int(data['topic_id'])
    uos = UserOefSurvey.objects.get(oef_survey_id=survey_id, user_id=request.user.id)
    answer = get_answer(uos, question_id) or create_answer(uos, data)
    return JsonResponse({
        'status': 'success'
    }, status=status.HTTP_201_CREATED)
