"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from survey_questions import exit_survey_questions

class ExitSurveyTest(TestCase):
    
    def test_unique_names(self):
        question_names = set()
        for question in exit_survey_questions['common_questions'] + exit_survey_questions['random_questions']:
            name = question['question_name']
            self.assertFalse( name in question_names, "There is a duplicate of name " + name )
            question_names.add(name)
            
    def test_question_format(self):
        for question in exit_survey_questions['common_questions'] + exit_survey_questions['random_questions']:
            self.assertTrue( 'question_name' in question, "All questions need a question_name. Failed on: "  + str(question) )
            self.assertTrue( 'label' in question, "All questions need a label. Failed on: "  + str(question) )
            
            question_type = question['type']
            
            if question_type == 'checkbox' or question_type == 'short_field' or question_type == 'medium_field':
                # No other required fields
                pass
            elif question_type == 'radio' or question_type == 'select_many':
                self.assertTrue( 'choices' in question, "All radio/select_many questions need choices. Failed on: "  + str(question) )
            else:
                self.assertTrue(False, "Found illegal question type. Failed on: " + str(question) )
