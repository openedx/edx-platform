from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status

from lms.djangoapps.oef.models import OefSurvey, TopicQuestion


def fetch_survey(request):
    survey = OefSurvey.objects.filter(is_enabled=True).latest('created')
    topics = get_survey_topics(survey.id)

    return render(request, 'oef/oef_survey.html', {"topics": topics})


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
