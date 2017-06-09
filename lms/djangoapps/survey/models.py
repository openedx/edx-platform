"""
Models to support Course Surveys feature
"""

import logging
from lxml import etree
from collections import OrderedDict
from django.db import models
from student.models import User
from django.core.exceptions import ValidationError

from model_utils.models import TimeStampedModel

from survey.exceptions import SurveyFormNameAlreadyExists, SurveyFormNotFound

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField

log = logging.getLogger("edx.survey")


class SurveyForm(TimeStampedModel):
    """
    Model to define a Survey Form that contains the HTML form data
    that is presented to the end user. A SurveyForm is not tied to
    a particular run of a course, to allow for sharing of Surveys
    across courses
    """
    name = models.CharField(max_length=255, db_index=True, unique=True)
    form = models.TextField()

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Override save method so we can validate that the form HTML is
        actually parseable
        """

        self.validate_form_html(self.form)

        # now call the actual save method
        super(SurveyForm, self).save(*args, **kwargs)

    @classmethod
    def validate_form_html(cls, html):
        """
        Makes sure that the html that is contained in the form field is valid
        """
        try:
            fields = cls.get_field_names_from_html(html)
        except Exception as ex:
            log.exception("Cannot parse SurveyForm html: {}".format(ex))
            raise ValidationError("Cannot parse SurveyForm as HTML: {}".format(ex))

        if not len(fields):
            raise ValidationError("SurveyForms must contain at least one form input field")

    @classmethod
    def create(cls, name, form, update_if_exists=False):
        """
        Helper class method to create a new Survey Form.

        update_if_exists=True means that if a form already exists with that name, then update it.
        Otherwise throw an SurveyFormAlreadyExists exception
        """

        survey = cls.get(name, throw_if_not_found=False)
        if not survey:
            survey = SurveyForm(name=name, form=form)
        else:
            if update_if_exists:
                survey.form = form
            else:
                raise SurveyFormNameAlreadyExists()

        survey.save()
        return survey

    @classmethod
    def get(cls, name, throw_if_not_found=True):
        """
        Helper class method to look up a Survey Form, throw FormItemNotFound if it does not exists
        in the database, unless throw_if_not_found=False then we return None
        """

        survey = None
        exists = SurveyForm.objects.filter(name=name).exists()
        if exists:
            survey = SurveyForm.objects.get(name=name)
        elif throw_if_not_found:
            raise SurveyFormNotFound()

        return survey

    def get_answers(self, user=None, limit_num_users=10000):
        """
        Returns all answers for all users for this Survey
        """
        return SurveyAnswer.get_answers(self, user, limit_num_users=limit_num_users)

    def has_user_answered_survey(self, user):
        """
        Returns whether a given user has supplied answers to this
        survey
        """
        return SurveyAnswer.do_survey_answers_exist(self, user)

    def save_user_answers(self, user, answers, course_key):
        """
        Store answers to the form for a given user. Answers is a dict of simple
        name/value pairs

        IMPORTANT: There is no validaton of form answers at this point. All data
        supplied to this method is presumed to be previously validated
        """

        # first remove any answer the user might have done before
        self.clear_user_answers(user)
        SurveyAnswer.save_answers(self, user, answers, course_key)

    def clear_user_answers(self, user):
        """
        Removes all answers that a user has submitted
        """
        SurveyAnswer.objects.filter(form=self, user=user).delete()

    def get_field_names(self):
        """
        Returns a list of defined field names for all answers in a survey. This can be
        helpful for reporting like features, i.e. adding headers to the reports
        This is taken from the set of <input> fields inside the form.
        """

        return SurveyForm.get_field_names_from_html(self.form)

    @classmethod
    def get_field_names_from_html(cls, html):
        """
        Returns a list of defined field names from a block of HTML
        """
        names = []

        # make sure the form is wrap in some outer single element
        # otherwise lxml can't parse it
        # NOTE: This wrapping doesn't change the ability to query it
        tree = etree.fromstring(u'<div>{}</div>'.format(html))

        input_fields = (
            tree.findall('.//input') + tree.findall('.//select') +
            tree.findall('.//textarea')
        )

        for input_field in input_fields:
            if 'name' in input_field.keys() and input_field.attrib['name'] not in names:
                names.append(input_field.attrib['name'])

        return names


class SurveyAnswer(TimeStampedModel):
    """
    Model for the answers that a user gives for a particular form in a course
    """
    user = models.ForeignKey(User, db_index=True)
    form = models.ForeignKey(SurveyForm, db_index=True)
    field_name = models.CharField(max_length=255, db_index=True)
    field_value = models.CharField(max_length=1024)

    # adding the course_id where the end-user answered the survey question
    # since it didn't exist in the beginning, it is nullable
    course_key = CourseKeyField(max_length=255, db_index=True, null=True)

    @classmethod
    def do_survey_answers_exist(cls, form, user):
        """
        Returns whether a user has any answers for a given SurveyForm for a course
        This can be used to determine if a user has taken a CourseSurvey.
        """
        return SurveyAnswer.objects.filter(form=form, user=user).exists()

    @classmethod
    def get_answers(cls, form, user=None, limit_num_users=10000):
        """
        Returns all answers a user (or all users, when user=None) has given to an instance of a SurveyForm

        Return is a nested dict which are simple name/value pairs with an outer key which is the
        user id. For example (where 'field3' is an optional field):

        results = {
            '1': {
                'field1': 'value1',
                'field2': 'value2',
            },
            '2': {
                'field1': 'value3',
                'field2': 'value4',
                'field3': 'value5',
            }
            :
            :
        }

        limit_num_users is to prevent an unintentional huge, in-memory dictionary.
        """

        if user:
            answers = SurveyAnswer.objects.filter(form=form, user=user)
        else:
            answers = SurveyAnswer.objects.filter(form=form)

        results = OrderedDict()
        num_users = 0
        for answer in answers:
            user_id = answer.user.id
            if user_id not in results and num_users < limit_num_users:
                results[user_id] = OrderedDict()
                num_users = num_users + 1

            if user_id in results:
                results[user_id][answer.field_name] = answer.field_value

        return results

    @classmethod
    def save_answers(cls, form, user, answers, course_key):
        """
        Store answers to the form for a given user. Answers is a dict of simple
        name/value pairs

        IMPORTANT: There is no validaton of form answers at this point. All data
        supplied to this method is presumed to be previously validated
        """
        for name in answers.keys():
            value = answers[name]

            # See if there is an answer stored for this user, form, field_name pair or not
            # this will allow for update cases. This does include an additional lookup,
            # but write operations will be relatively infrequent
            value = answers[name]
            defaults = {"field_value": value}
            if course_key:
                defaults['course_key'] = course_key

            answer, created = SurveyAnswer.objects.get_or_create(
                user=user,
                form=form,
                field_name=name,
                defaults=defaults
            )

            if not created:
                # Allow for update cases.
                answer.field_value = value
                answer.course_key = course_key
                answer.save()
