import datetime
import json

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status

from lms.djangoapps.oef.models import OefSurvey, TopicQuestion, UserOefSurvey, UserAnswers, OptionPriority


def fetch_survey(request):
    latest_survey = OefSurvey.objects.filter(is_enabled=True).latest('created')
    uos = get_user_survey(request.user, latest_survey)
    survey = uos.oef_survey
    topics = get_survey_topics(uos, survey.id)
    priorities = get_option_priorities()
    return render(request, 'oef/oef_survey.html', {"survey_id": survey.id,
                                                   "topics": topics,
                                                   "priorities": priorities
                                                   })


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
        options = topic.options.all()
        options = {str(option.priority.value).replace('.', ''): get_option_data(option) for option in options}
        parsed_topics.append({
            'title': topic.title,
            'description': topic.description,
            'index': index + 1,
            'id': topic.id,
            'options': options,
            'answer': get_answer(uos, topic.id)
        })
    return parsed_topics


def get_option_priorities():
    priorities = list(OptionPriority.objects.all())
    priorities.sort(key=lambda x: x.value, reverse=False)
    return priorities


def get_option_data(option):
    return {
        'text': option.text,
        'priority': option.priority.label,
        'id': option.id
    }


def get_answer(uos, question_id):
    try:
        return UserAnswers.objects.get(user_survey_id=uos.id, question_id=question_id).selected_option.value
    except UserAnswers.DoesNotExist:
        return None


def create_answer(uos, data):
    answer = UserAnswers()
    answer.user_survey = uos
    answer.question_id = int(data['topic_id'])
    return answer


def get_option(option_value):
    return OptionPriority.objects.get(value=option_value)


def save_answer(request):
    data = json.loads(request.body)
    survey_id = int(data['survey_id'])
    uos = UserOefSurvey.objects.get(oef_survey_id=survey_id, user_id=request.user.id)

    for answer_data in data['answers']:
        question_id = int(answer_data['topic_id'])

        answer = get_answer(uos, question_id) or create_answer(uos, answer_data)
        answer.selected_option = get_option(float(answer_data['answer_id']))
        answer.save()
    return JsonResponse({
        'status': 'success'
    }, status=status.HTTP_201_CREATED)
