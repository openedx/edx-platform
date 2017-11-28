import datetime

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status

from lms.djangoapps.oef.models import OefSurvey, TopicQuestion, UserOefSurvey, UserAnswers


def fetch_survey(request):
    latest_survey = OefSurvey.objects.filter(is_enabled=True).latest('created')
    uos = get_user_survey(request.user, latest_survey)
    survey = uos.oef_survey
    topics = get_survey_topics(uos, survey.id)

    return render(request, 'oef/oef_survey.html', {"survey_id": survey.id, "topics": topics})


def get_user_survey(user, latest_survey):
    try:
        uos = UserOefSurvey.objects.get(user_id=user.id, status='in-progress')
    except UserOefSurvey.DoesNotExist:
        uos = UserOefSurvey()
        uos.oef_survey = latest_survey
        uos.user = user
        uos.survey_date = datetime.date.today()
        uos.start_date = datetime.date.today()
        uos.completed_date = datetime.date.today()
        uos.save()

    return uos


def is_answered(uos, question_id):
    return UserAnswers.objects.filter(user_survey_id=uos.id).filter(question_id=question_id).exists()


def get_survey_topics(uos, survey_id):
    topics = TopicQuestion.objects.filter(survey_id=survey_id)
    parsed_topics = []
    for index, topic in enumerate(topics):
        parsed_topics.append({
            'title': topic.title,
            'index': index + 1,
            'id': topic.id,
            'is_answered': is_answered(uos, topic.id)
        })
    return parsed_topics


def get_option_data(option):
    return {
        'text': option.text,
        'priority': option.priority.label,
        'id': option.id
    }


def get_survey_topic(request, survey_id, topic_id):
    topic_question = TopicQuestion.objects.get(id=topic_id)
    options = topic_question.options.all()
    options = [get_option_data(option) for option in options]
    uos = UserOefSurvey.objects.get(oef_survey_id=survey_id, user_id=request.user.id)
    answer = get_answer(uos, topic_id)
    answer = str(answer.selected_option.value) if answer else ''

    return JsonResponse({
        'title': topic_question.title,
        'description': topic_question.description,
        'id': topic_question.id,
        'options': options,
        'answer': answer.replace('.0', '')
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
    return answer


def save_answer(request):
    data = request.POST
    survey_id = int(data['survey_id'])
    question_id = int(data['topic_id'])
    uos = UserOefSurvey.objects.get(oef_survey_id=survey_id, user_id=request.user.id)
    answer = get_answer(uos, question_id) or create_answer(uos, data)
    answer.selected_option_id = int(data['answer'])
    answer.save()
    return JsonResponse({
        'status': 'success'
    }, status=status.HTTP_201_CREATED)
