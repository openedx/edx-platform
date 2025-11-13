"""
AI Tutor XBlock.

This XBlock provides a chat interface where students can interact with
an AI-powered tutor for real-time help and explanations.
"""

import json
import logging
from datetime import datetime
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
class AITutorXBlock(StudioEditableXBlockMixin, XBlock):
    """
    An AI-powered tutoring interface that provides real-time assistance
    to students through natural language conversation.
    """

    display_name = String(
        display_name="Display Name",
        default="AI Tutor",
        scope=Scope.settings,
        help="The display name for this component."
    )

    tutor_persona = String(
        display_name="Tutor Persona",
        default="friendly_mentor",
        scope=Scope.settings,
        values=[
            {"display_name": "Friendly Mentor", "value": "friendly_mentor"},
            {"display_name": "Socratic Teacher", "value": "socratic"},
            {"display_name": "Expert Professor", "value": "expert"},
            {"display_name": "Peer Tutor", "value": "peer"},
        ],
        help="The personality style of the AI tutor"
    )

    welcome_message = String(
        display_name="Welcome Message",
        default="Hello! I'm your AI tutor. How can I help you today?",
        scope=Scope.settings,
        help="Initial message shown to students",
        multiline_editor=True
    )

    max_message_length = Integer(
        display_name="Max Message Length",
        default=500,
        scope=Scope.settings,
        help="Maximum length of student messages"
    )

    enable_conversation_history = Boolean(
        display_name="Enable Conversation History",
        default=True,
        scope=Scope.settings,
        help="Store and display previous conversation history"
    )

    # Student state
    conversation_history = List(
        default=[],
        scope=Scope.user_state,
        help="Conversation history for this student"
    )

    message_count = Integer(
        default=0,
        scope=Scope.user_state,
        help="Number of messages sent by student"
    )

    editable_fields = (
        'display_name',
        'tutor_persona',
        'welcome_message',
        'max_message_length',
        'enable_conversation_history'
    )

    def student_view(self, context=None):
        """
        The primary view of the XBlock, shown to students.
        """
        context = context or {}

        # Add welcome message to history if empty
        if not self.conversation_history and self.welcome_message:
            self.conversation_history = [{
                'role': 'assistant',
                'message': self.welcome_message,
                'timestamp': datetime.utcnow().isoformat()
            }]

        context.update({
            'display_name': self.display_name,
            'conversation_history': self.conversation_history,
            'max_message_length': self.max_message_length,
            'message_count': self.message_count,
        })

        html = loader.render_django_template(
            'templates/ai_tutor.html',
            context
        )

        frag = Fragment(html)
        frag.add_css(loader.load_unicode('static/css/ai_tutor.css'))
        frag.add_javascript(loader.load_unicode('static/js/ai_tutor.js'))
        frag.initialize_js('AITutorXBlock')

        return frag

    @XBlock.json_handler
    def send_message(self, data, suffix=''):
        """
        Handle a message from the student and get AI tutor response.
        """
        message = data.get('message', '').strip()

        if not message:
            return {
                'success': False,
                'error': 'Message cannot be empty'
            }

        if len(message) > self.max_message_length:
            return {
                'success': False,
                'error': f'Message too long (max {self.max_message_length} characters)'
            }

        try:
            user_service = self.runtime.service(self, 'user')
            user = user_service.get_current_user()

            # Add student message to history
            student_message = {
                'role': 'student',
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }

            if self.enable_conversation_history:
                self.conversation_history.append(student_message)

            self.message_count += 1

            # Get AI tutor response
            response_data = ai_api.get_ai_tutor_response(
                user=user,
                course_key=self.course_id,
                usage_key=self.location,
                message=message,
                conversation_history=self.conversation_history if self.enable_conversation_history else []
            )

            # Add tutor response to history
            tutor_message = {
                'role': 'assistant',
                'message': response_data.get('response', 'I apologize, but I\'m having trouble responding right now.'),
                'timestamp': datetime.utcnow().isoformat(),
                'confidence': response_data.get('confidence'),
                'sources': response_data.get('sources', [])
            }

            if self.enable_conversation_history:
                self.conversation_history.append(tutor_message)

            # Trim history if it gets too long (keep last 50 messages)
            if len(self.conversation_history) > 50:
                # Keep welcome message and last 49 messages
                self.conversation_history = [
                    self.conversation_history[0]
                ] + self.conversation_history[-49:]

            # Record interaction
            ai_api.record_adaptive_interaction(
                user=user,
                course_key=self.course_id,
                usage_key=self.location,
                interaction_type='tutor_chat',
                interaction_data={
                    'message': message,
                    'response': tutor_message['message'],
                    'message_count': self.message_count
                }
            )

            return {
                'success': True,
                'student_message': student_message,
                'tutor_message': tutor_message,
                'message_count': self.message_count
            }

        except Exception as e:
            log.error(f"Error in AI tutor: {e}", exc_info=True)
            return {
                'success': False,
                'error': 'Unable to get response from AI tutor. Please try again.'
            }

    @XBlock.json_handler
    def clear_history(self, data, suffix=''):
        """
        Clear the conversation history for this student.
        """
        self.conversation_history = []
        self.message_count = 0

        # Re-add welcome message
        if self.welcome_message:
            self.conversation_history = [{
                'role': 'assistant',
                'message': self.welcome_message,
                'timestamp': datetime.utcnow().isoformat()
            }]

        return {
            'success': True,
            'message': 'Conversation history cleared.'
        }

    @XBlock.json_handler
    def get_hint(self, data, suffix=''):
        """
        Get a contextual hint about the current lesson.
        """
        try:
            user_service = self.runtime.service(self, 'user')
            user = user_service.get_current_user()

            hint_response = ai_api.get_ai_tutor_response(
                user=user,
                course_key=self.course_id,
                usage_key=self.location,
                message="Can you give me a hint about this topic?",
                conversation_history=self.conversation_history if self.enable_conversation_history else []
            )

            return {
                'success': True,
                'hint': hint_response.get('response', 'No hint available at this time.')
            }

        except Exception as e:
            log.error(f"Error getting hint: {e}", exc_info=True)
            return {
                'success': False,
                'error': 'Unable to generate hint.'
            }

    @staticmethod
    def workbench_scenarios():
        """
        Scenarios for testing in workbench.
        """
        return [
            ("AI Tutor - Friendly Mentor", """
                <ai_tutor
                    display_name="AI Tutor"
                    tutor_persona="friendly_mentor"
                    welcome_message="Hi! I'm here to help you learn. What would you like to know?"
                    enable_conversation_history="true"
                />
            """),
            ("AI Tutor - Socratic", """
                <ai_tutor
                    display_name="Socratic Tutor"
                    tutor_persona="socratic"
                    welcome_message="Welcome. What questions do you have about this material?"
                    enable_conversation_history="true"
                />
            """),
        ]
