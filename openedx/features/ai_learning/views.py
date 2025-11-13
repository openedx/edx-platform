"""
Views and API endpoints for AI Learning integration.
"""

import hashlib
import hmac
import logging
from typing import Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.lib.api.authentication import BearerAuthentication
from openedx.core.lib.api.permissions import IsStaff

from . import api as ai_api
from .client import AIEngineClient, AIEngineClientError
from .models import AIEngineWebhook
from .serializers import (
    AdaptiveFeedbackRequestSerializer,
    AITutorRequestSerializer,
    CourseGenerationRequestSerializer,
    InteractionRecordSerializer,
)

User = get_user_model()
log = logging.getLogger(__name__)


class GenerateCourseView(APIView):
    """
    API endpoint to request AI-powered course generation.

    POST /ai-learning/api/v1/courses/generate/
    """
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsAuthenticated, IsStaff)

    def post(self, request):
        """
        Generate a new course using AI Engine.

        Request body:
        {
            "prompt": "Create a PhD-level course on Quantum Field Theory",
            "course_org": "MIT",
            "course_number": "8.323",
            "course_run": "2025_Spring",
            "metadata": {...}
        }
        """
        serializer = CourseGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            ai_course = ai_api.generate_course(
                user=request.user,
                prompt=serializer.validated_data['prompt'],
                course_org=serializer.validated_data['course_org'],
                course_number=serializer.validated_data['course_number'],
                course_run=serializer.validated_data['course_run'],
                metadata=serializer.validated_data.get('metadata')
            )

            return Response({
                'course_key': str(ai_course.course_key),
                'ai_engine_course_id': ai_course.ai_engine_course_id,
                'status': ai_course.generation_status,
                'message': 'Course generation started successfully'
            }, status=status.HTTP_202_ACCEPTED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except RuntimeError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecordInteractionView(APIView):
    """
    API endpoint for XBlocks to record adaptive interactions.

    POST /ai-learning/api/v1/interactions/record/
    """
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Record an adaptive interaction from an XBlock.

        Request body:
        {
            "course_key": "course-v1:edX+DemoX+Demo_Course",
            "usage_key": "block-v1:edX+DemoX+Demo_Course+type@problem+block@...",
            "interaction_type": "assessment",
            "interaction_data": {...}
        }
        """
        serializer = InteractionRecordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            course_key = CourseKey.from_string(serializer.validated_data['course_key'])
            usage_key = UsageKey.from_string(serializer.validated_data['usage_key'])

            interaction = ai_api.record_adaptive_interaction(
                user=request.user,
                course_key=course_key,
                usage_key=usage_key,
                interaction_type=serializer.validated_data['interaction_type'],
                interaction_data=serializer.validated_data['interaction_data']
            )

            return Response({
                'interaction_id': interaction.id,
                'ai_response': interaction.ai_response,
                'response_time_ms': interaction.response_time_ms
            }, status=status.HTTP_201_CREATED)

        except InvalidKeyError as e:
            return Response(
                {'error': f'Invalid key: {e}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            log.error(f"Error recording interaction: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to record interaction'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdaptiveFeedbackView(APIView):
    """
    API endpoint to get adaptive feedback for assessments.

    POST /ai-learning/api/v1/feedback/
    """
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Get personalized feedback for a student's answer.

        Request body:
        {
            "course_key": "course-v1:edX+DemoX+Demo_Course",
            "usage_key": "block-v1:...",
            "question": {...},
            "answer": {...}
        }
        """
        serializer = AdaptiveFeedbackRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            course_key = CourseKey.from_string(serializer.validated_data['course_key'])
            usage_key = UsageKey.from_string(serializer.validated_data['usage_key'])

            feedback = ai_api.get_adaptive_feedback(
                user=request.user,
                course_key=course_key,
                usage_key=usage_key,
                question_data=serializer.validated_data['question'],
                answer_data=serializer.validated_data['answer']
            )

            return Response(feedback, status=status.HTTP_200_OK)

        except InvalidKeyError as e:
            return Response(
                {'error': f'Invalid key: {e}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            log.error(f"Error getting feedback: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to generate feedback'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AITutorChatView(APIView):
    """
    API endpoint for AI tutor chat interactions.

    POST /ai-learning/api/v1/tutor/chat/
    """
    authentication_classes = (BearerAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Get AI tutor response to student message.

        Request body:
        {
            "course_key": "course-v1:edX+DemoX+Demo_Course",
            "usage_key": "block-v1:...",
            "message": "Can you explain quantum entanglement?",
            "conversation_history": [...]
        }
        """
        serializer = AITutorRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            course_key = CourseKey.from_string(serializer.validated_data['course_key'])
            usage_key = UsageKey.from_string(serializer.validated_data['usage_key'])

            response_data = ai_api.get_ai_tutor_response(
                user=request.user,
                course_key=course_key,
                usage_key=usage_key,
                message=serializer.validated_data['message'],
                conversation_history=serializer.validated_data.get('conversation_history')
            )

            return Response(response_data, status=status.HTTP_200_OK)

        except InvalidKeyError as e:
            return Response(
                {'error': f'Invalid key: {e}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            log.error(f"Error getting tutor response: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to get tutor response'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AIEngineWebhookView(APIView):
    """
    Webhook endpoint for receiving events from AI Engine.

    POST /ai-learning/webhooks/ai-engine/
    """
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        """
        Handle webhook from AI Engine.

        Expected headers:
        - X-AI-Engine-Signature: HMAC signature of payload

        Request body:
        {
            "event_type": "course_generation_complete",
            "data": {...}
        }
        """
        # Verify webhook signature
        if not self._verify_signature(request):
            log.warning("Invalid webhook signature")
            return Response(
                {'error': 'Invalid signature'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Log webhook
        webhook = AIEngineWebhook.objects.create(
            webhook_type=request.data.get('event_type', 'unknown'),
            payload=request.data,
            status='received'
        )

        try:
            event_type = request.data.get('event_type')
            data = request.data.get('data', {})

            # Route to appropriate handler
            handler = self._get_handler(event_type)
            if handler:
                webhook.status = 'processing'
                webhook.save()

                handler(data)

                webhook.status = 'completed'
                webhook.save()

                return Response({'status': 'processed'}, status=status.HTTP_200_OK)
            else:
                webhook.status = 'completed'
                webhook.error_message = f'No handler for event type: {event_type}'
                webhook.save()

                return Response(
                    {'status': 'ignored', 'reason': 'Unknown event type'},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            log.error(f"Webhook processing error: {e}", exc_info=True)
            webhook.status = 'failed'
            webhook.error_message = str(e)
            webhook.save()

            return Response(
                {'error': 'Processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _verify_signature(self, request) -> bool:
        """Verify HMAC signature of webhook payload."""
        signature = request.headers.get('X-AI-Engine-Signature', '')
        secret = settings.AI_LEARNING_WEBHOOK_SECRET

        if not secret:
            log.warning("Webhook secret not configured")
            return False

        # Compute expected signature
        payload = request.body
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def _get_handler(self, event_type: str):
        """Get handler function for event type."""
        handlers = {
            'course_generation_complete': self._handle_course_generation_complete,
            'course_generation_failed': self._handle_course_generation_failed,
            'student_profile_updated': self._handle_student_profile_updated,
            'adaptation_triggered': self._handle_adaptation_triggered,
        }
        return handlers.get(event_type)

    def _handle_course_generation_complete(self, data: Dict):
        """Handle course generation completion."""
        from .models import AIGeneratedCourse

        course_key = CourseKey.from_string(data['course_key'])
        ai_course = AIGeneratedCourse.objects.get(course_key=course_key)
        ai_course.generation_status = 'completed'
        ai_course.curriculum_data = data.get('curriculum', {})
        ai_course.save()

        log.info(f"Course generation completed: {course_key}")

    def _handle_course_generation_failed(self, data: Dict):
        """Handle course generation failure."""
        from .models import AIGeneratedCourse

        course_key = CourseKey.from_string(data['course_key'])
        ai_course = AIGeneratedCourse.objects.get(course_key=course_key)
        ai_course.generation_status = 'failed'
        ai_course.metadata['error'] = data.get('error', 'Unknown error')
        ai_course.save()

        log.error(f"Course generation failed: {course_key}")

    def _handle_student_profile_updated(self, data: Dict):
        """Handle student profile update from AI Engine."""
        user_id = data['user_id']
        user = User.objects.get(id=user_id)
        ai_api.sync_student_profile(user)

        log.info(f"Student profile synced: {user_id}")

    def _handle_adaptation_triggered(self, data: Dict):
        """Handle adaptation trigger from AI Engine."""
        # This would trigger course structure modifications
        # Implementation depends on specific adaptation requirements
        log.info(f"Adaptation triggered: {data}")


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaff])
def health_check(request):
    """
    Check health of AI Engine connection.

    GET /ai-learning/api/v1/health/
    """
    try:
        client = AIEngineClient()
        health = client.health_check()

        return Response({
            'ai_engine': health,
            'integration': 'healthy'
        }, status=status.HTTP_200_OK)

    except AIEngineClientError as e:
        return Response({
            'ai_engine': {'status': 'unhealthy', 'error': str(e)},
            'integration': 'healthy'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
