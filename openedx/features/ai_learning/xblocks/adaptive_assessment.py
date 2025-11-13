"""
Adaptive Assessment XBlock.

This XBlock presents assessment questions that adapt based on student performance.
It communicates with the AI Engine to get personalized feedback and determine
next steps in the learning path.
"""

import json
import logging
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Integer, Scope, String, Dict, List, Boolean
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from openedx.features.ai_learning import api as ai_api

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


@XBlock.needs('i18n')
@XBlock.needs('user')
class AdaptiveAssessmentXBlock(StudioEditableXBlockMixin, XBlock):
    """
    An adaptive assessment that provides personalized feedback and adapts
    difficulty based on student performance.
    """

    display_name = String(
        display_name="Display Name",
        default="Adaptive Assessment",
        scope=Scope.settings,
        help="The display name for this component."
    )

    question_text = String(
        display_name="Question",
        default="",
        scope=Scope.content,
        help="The question to present to students",
        multiline_editor=True
    )

    question_type = String(
        display_name="Question Type",
        default="multiple_choice",
        scope=Scope.content,
        values=[
            {"display_name": "Multiple Choice", "value": "multiple_choice"},
            {"display_name": "Short Answer", "value": "short_answer"},
            {"display_name": "Numeric", "value": "numeric"},
        ],
        help="The type of question"
    )

    options = List(
        display_name="Answer Options",
        default=[],
        scope=Scope.content,
        help="List of answer options (for multiple choice)"
    )

    correct_answer = String(
        display_name="Correct Answer",
        default="",
        scope=Scope.content,
        help="The correct answer or answer key"
    )

    enable_ai_feedback = Boolean(
        display_name="Enable AI Feedback",
        default=True,
        scope=Scope.settings,
        help="Enable personalized AI-generated feedback"
    )

    # Student state
    student_answer = String(
        default="",
        scope=Scope.user_state,
        help="Student's submitted answer"
    )

    attempts = Integer(
        default=0,
        scope=Scope.user_state,
        help="Number of attempts"
    )

    is_correct = Boolean(
        default=False,
        scope=Scope.user_state,
        help="Whether the answer is correct"
    )

    ai_feedback = Dict(
        default={},
        scope=Scope.user_state,
        help="AI-generated feedback for the student"
    )

    editable_fields = (
        'display_name',
        'question_text',
        'question_type',
        'options',
        'correct_answer',
        'enable_ai_feedback'
    )

    def student_view(self, context=None):
        """
        The primary view of the XBlock, shown to students.
        """
        context = context or {}
        context.update({
            'display_name': self.display_name,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'options': self.options,
            'student_answer': self.student_answer,
            'attempts': self.attempts,
            'is_correct': self.is_correct,
            'ai_feedback': self.ai_feedback,
            'enable_ai_feedback': self.enable_ai_feedback,
        })

        html = loader.render_django_template(
            'templates/adaptive_assessment.html',
            context
        )

        frag = Fragment(html)
        frag.add_css(loader.load_unicode('static/css/adaptive_assessment.css'))
        frag.add_javascript(loader.load_unicode('static/js/adaptive_assessment.js'))
        frag.initialize_js('AdaptiveAssessmentXBlock')

        return frag

    @XBlock.json_handler
    def submit_answer(self, data, suffix=''):
        """
        Handle answer submission from student.
        """
        import time
        start_time = time.time()

        student_answer = data.get('answer', '')
        self.student_answer = student_answer
        self.attempts += 1

        # Check if answer is correct
        is_correct = self._check_answer(student_answer)
        self.is_correct = is_correct

        response = {
            'success': True,
            'is_correct': is_correct,
            'attempts': self.attempts,
        }

        # Get AI-powered feedback if enabled
        if self.enable_ai_feedback:
            try:
                user_service = self.runtime.service(self, 'user')
                user = user_service.get_current_user()

                # Prepare interaction data
                interaction_data = {
                    'question': {
                        'text': self.question_text,
                        'type': self.question_type,
                        'options': self.options,
                    },
                    'answer': {
                        'value': student_answer,
                        'is_correct': is_correct,
                        'attempts': self.attempts,
                        'time_taken': int((time.time() - start_time) * 1000),
                    }
                }

                # Get adaptive feedback from AI Engine
                feedback = ai_api.get_adaptive_feedback(
                    user=user,
                    course_key=self.course_id,
                    usage_key=self.location,
                    question_data=interaction_data['question'],
                    answer_data=interaction_data['answer']
                )

                self.ai_feedback = feedback
                response['feedback'] = feedback.get('feedback', '')
                response['hints'] = feedback.get('hints', [])
                response['adaptations'] = feedback.get('adaptations', [])

                # Record the interaction
                ai_api.record_adaptive_interaction(
                    user=user,
                    course_key=self.course_id,
                    usage_key=self.location,
                    interaction_type='assessment',
                    interaction_data=interaction_data
                )

            except Exception as e:
                log.error(f"Error getting AI feedback: {e}", exc_info=True)
                response['feedback'] = 'Unable to generate personalized feedback at this time.'

        else:
            # Provide basic feedback
            if is_correct:
                response['feedback'] = 'Correct! Well done.'
            else:
                response['feedback'] = 'Incorrect. Please try again.'

        return response

    def _check_answer(self, student_answer):
        """
        Check if the student's answer is correct.

        This is a simple implementation. In production, you might want
        more sophisticated answer checking, especially for open-ended questions.
        """
        if self.question_type == 'multiple_choice':
            return student_answer == self.correct_answer

        elif self.question_type == 'numeric':
            try:
                student_num = float(student_answer)
                correct_num = float(self.correct_answer)
                # Allow for small floating point differences
                return abs(student_num - correct_num) < 0.01
            except (ValueError, TypeError):
                return False

        elif self.question_type == 'short_answer':
            # Case-insensitive comparison, strip whitespace
            return student_answer.strip().lower() == self.correct_answer.strip().lower()

        return False

    @XBlock.json_handler
    def reset(self, data, suffix=''):
        """
        Reset the student's state for this problem.
        """
        self.student_answer = ""
        self.attempts = 0
        self.is_correct = False
        self.ai_feedback = {}

        return {
            'success': True,
            'message': 'Assessment has been reset.'
        }

    @staticmethod
    def workbench_scenarios():
        """
        A handful of scenarios for testing in workbench.
        """
        return [
            ("Adaptive Assessment - Multiple Choice", """
                <adaptive_assessment
                    display_name="Adaptive Assessment"
                    question_text="What is 2 + 2?"
                    question_type="multiple_choice"
                    options='["3", "4", "5", "6"]'
                    correct_answer="4"
                    enable_ai_feedback="true"
                />
            """),
            ("Adaptive Assessment - Short Answer", """
                <adaptive_assessment
                    display_name="Short Answer Assessment"
                    question_text="What is the capital of France?"
                    question_type="short_answer"
                    correct_answer="Paris"
                    enable_ai_feedback="true"
                />
            """),
        ]
