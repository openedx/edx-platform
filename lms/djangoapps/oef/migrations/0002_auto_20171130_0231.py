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
    'Human Resource Management',
    'Leadership & Governance',
    'Financial Management',
    'Fundraising & Resource Mobilization',
    'Measurement, Evaluation & Learning',
    'Marketing Communications & PR',
    'Strategy & Planning',
    'Program Design & Delivery',
    'External Relations & Partnerships',
    'System Tools & Processes',
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
        tq = topic_question(survey=survey, title=t, description=TOPIC_TEXT % t)
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
                                class="link has-border oef-questionnaire" href="#">Start OEF here</a></p>

                        <p class="mt40">This is the final step in the registration process!</p>
                        <p>Click to open each of the 10 areas of organizational effectiveness using the <span class="circle-text-icon">+</span>.
                             For each area, select the button closest to the box which best
                            describes your organization’s capacity in that area, based on the examples provided. If you
                            want more information than the examples provided, click the <span class="see-more-text-icon">SEE MORE</span> and more
                            information will drop down. In some cases, you may find that there is not a box that
                            perfectly describes the state of your organization - select the box that most closely
                            describes your organization.</p>

                        <p>If you think that your organization’s capacity sits between two levels, select the <span class="circle-text-icon">+/-</span>
                             which sits between each level. For example, if you believe your organization is
                            more effective than the box which describes level 3 for the Human resource management area,
                            but not quite a level 4, you can select the <span class="circle-text-icon">+/-</span> which sits between 3 and
                            4.</p>

                        <p>Remember that you can start the OEF, complete part of it, save it as a draft, and return to
                            complete it when you have time. There is no deadline for completion.</p>

                        <p>If you have questions, check out the OEF Q&A.</p>
""")
        survey_obj.save()
        create_topics(apps, survey_obj, level_models)

    dependencies = [
        ('oef', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_required_tables),
    ]
