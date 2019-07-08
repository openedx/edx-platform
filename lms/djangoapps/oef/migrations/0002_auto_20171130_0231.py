# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

LEVELS = [
    {
        'label': 'Developing Capacity',
        'value': 1,
        'caption': '1'
    },
    {
        'label': 'Developing/Basic',
        'value': 1.5,
        'caption': '+/-'
    },
    {
        'label': 'Basic Capacity',
        'value': 2,
        'caption': '2'

    },
    {
        'label': 'Basic/Moderate',
        'value': 2.5,
        'caption': '+/-'
    },
    {
        'label': 'Moderate Capacity',
        'value': 3,
        'caption': '3'

    },
    {
        'label': 'Moderate/High',
        'value': 3.5,
        'caption': '+/-'
    },
    {
        'label': 'High Capacity',
        'value': 4,
        'caption': '4'

    }
]

TOPICS = [
    {'title': 'Human Resource Management', 'score_name': 'human_resource_score'},
    {'title': 'Leadership & Governance', 'score_name': 'leadership_score'},
    {'title': 'Financial Management', 'score_name': 'financial_management_score'},
    {'title': 'Fundraising & Resource Mobilization', 'score_name': 'fundraising_score'},
    {'title': 'Measurement, Evaluation & Learning', 'score_name': 'measurement_score'},
    {'title': 'Marketing Communications & PR', 'score_name': 'marketing_score'},
    {'title': 'Strategy & Planning', 'score_name': 'strategy_score'},
    {'title': 'Program Design & Delivery', 'score_name': 'program_design_score'},
    {'title': 'External Relations & Partnerships', 'score_name': 'external_relations_score'},
    {'title': 'System Tools & Processes', 'score_name': 'systems_score'},
]

TOPIC_TEXT = 'This section of the organization effectiveness will test how strong is your organization %s skill.' \
             'Choose one of the 4 rubrics that best represents your organization in the following themes. To choose ' \
             'one of the rubrics you just need to click on it. If you want to change your answer, just click on the ' \
             'new rubric you want to select and the first one will be deselected'

FIRST_OPTION = 'Does your organization fall in the basic category of this skill set'
SECOND_OPTION = 'Does your organization fall in the developing category of this skill set'
THIRD_OPTION = 'Does your organization fall in the moderatte category of this skill set'
FOURTH_OPTION = 'Does your organization fall in the high category of this skill set'


def create_topics(apps, survey, levels):
    topic_question = apps.get_model('oef', 'TopicQuestion')
    option = apps.get_model('oef', 'Option')
    for t in TOPICS:
        tq = topic_question(survey=survey, title=t['title'], description=TOPIC_TEXT % t['title'],
                            score_name=t['score_name'])
        tq.save()
        opt = option(topic=tq, text=FIRST_OPTION, level=levels[0]).save()
        option(topic=tq, text=SECOND_OPTION, level=levels[2]).save()
        option(topic=tq, text=THIRD_OPTION, level=levels[4]).save()
        option(topic=tq, text=FOURTH_OPTION, level=levels[6]).save()


def create_level_models(apps):
    created_objs = []
    level_model = apps.get_model("oef", "OptionLevel")
    for level_option in LEVELS:
        level_obj = level_model(**level_option)
        level_obj.save()
        created_objs.append(level_obj)
    return created_objs


class Migration(migrations.Migration):
    def populate_required_tables(apps, schema_editor):
        level_models = create_level_models(apps)
        survey = apps.get_model('oef', 'OefSurvey')
        survey_obj = survey(title='Organization Effectiveness Survey', is_enabled=True, description="""<h4>This page answers some questions you may have about the OEF assessment tool.</h4>
                        <p>If you're ready to start your OEF assessment, &nbsp; <a
                                class="link has-border oef-questionnaire" href="#">Start OEF here</a></p>""")
        survey_obj.save()
        create_topics(apps, survey_obj, level_models)

    dependencies = [
        ('oef', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_required_tables),
    ]
