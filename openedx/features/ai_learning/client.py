"""
HTTP client for communicating with the AI Engine.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


class AIEngineClientError(Exception):
    """Base exception for AI Engine client errors."""
    pass


class AIEngineClient:
    """
    Client for communicating with the external AI Engine microservices.

    This client handles:
    - Authentication with API keys
    - Retry logic for transient failures
    - Timeout configuration
    - Response validation
    - Error handling
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize the AI Engine client.

        Args:
            base_url: Base URL of the AI Engine API
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.AI_ENGINE_BASE_URL
        self.api_key = api_key or settings.AI_ENGINE_API_KEY
        self.timeout = timeout or settings.AI_ENGINE_TIMEOUT

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'OpenEdX-AI-Learning/1.0'
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the AI Engine.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            AIEngineClientError: If request fails
        """
        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout as e:
            log.error(f"AI Engine request timeout: {url}")
            raise AIEngineClientError(f"Request timeout: {e}") from e

        except requests.exceptions.HTTPError as e:
            log.error(f"AI Engine HTTP error: {e.response.status_code} - {url}")
            raise AIEngineClientError(
                f"HTTP {e.response.status_code}: {e.response.text}"
            ) from e

        except requests.exceptions.RequestException as e:
            log.error(f"AI Engine request failed: {url} - {e}")
            raise AIEngineClientError(f"Request failed: {e}") from e

        except ValueError as e:
            log.error(f"Invalid JSON response from AI Engine: {url}")
            raise AIEngineClientError(f"Invalid response format: {e}") from e

    # Curriculum Generation API

    def generate_curriculum(
        self,
        prompt: str,
        course_key: str,
        user_id: int,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Request curriculum generation from AI Engine.

        Args:
            prompt: Natural language course description
            course_key: Open edX course key
            user_id: User ID of course creator
            metadata: Additional metadata

        Returns:
            Dictionary with course_id and generation status
        """
        data = {
            'prompt': prompt,
            'course_key': course_key,
            'user_id': user_id,
            'metadata': metadata or {}
        }
        return self._make_request('POST', '/api/v1/curriculum/generate', data=data)

    def get_curriculum_status(self, course_id: str) -> Dict:
        """Get the status of curriculum generation."""
        return self._make_request('GET', f'/api/v1/curriculum/{course_id}/status')

    def get_curriculum_data(self, course_id: str) -> Dict:
        """Get the generated curriculum data."""
        return self._make_request('GET', f'/api/v1/curriculum/{course_id}')

    # Content Creation API

    def generate_lesson_content(
        self,
        course_id: str,
        module_id: str,
        lesson_id: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate content for a specific lesson.

        Args:
            course_id: AI Engine course ID
            module_id: Module identifier
            lesson_id: Lesson identifier
            context: Additional context for content generation

        Returns:
            Dictionary with generated content
        """
        data = {
            'course_id': course_id,
            'module_id': module_id,
            'lesson_id': lesson_id,
            'context': context or {}
        }
        return self._make_request('POST', '/api/v1/content/generate', data=data)

    def generate_assessment(
        self,
        course_id: str,
        module_id: str,
        lesson_id: str,
        question_type: str,
        difficulty: str = 'medium',
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate an assessment question.

        Args:
            course_id: AI Engine course ID
            module_id: Module identifier
            lesson_id: Lesson identifier
            question_type: Type of question (multiple_choice, short_answer, etc.)
            difficulty: Question difficulty level
            context: Additional context

        Returns:
            Dictionary with generated question
        """
        data = {
            'course_id': course_id,
            'module_id': module_id,
            'lesson_id': lesson_id,
            'question_type': question_type,
            'difficulty': difficulty,
            'context': context or {}
        }
        return self._make_request('POST', '/api/v1/content/assessment', data=data)

    # Student Profile API

    def create_student_profile(self, user_id: int, username: str) -> Dict:
        """Create a new student profile in AI Engine."""
        data = {
            'user_id': user_id,
            'username': username
        }
        return self._make_request('POST', '/api/v1/students/profile', data=data)

    def get_student_profile(self, user_id: int) -> Dict:
        """Get student profile data from AI Engine."""
        # Try cache first
        cache_key = f'ai_profile_{user_id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        data = self._make_request('GET', f'/api/v1/students/{user_id}/profile')

        # Cache for 5 minutes
        cache.set(cache_key, data, 300)
        return data

    def update_student_profile(self, user_id: int, profile_data: Dict) -> Dict:
        """Update student profile data."""
        # Invalidate cache
        cache.delete(f'ai_profile_{user_id}')

        return self._make_request(
            'PUT',
            f'/api/v1/students/{user_id}/profile',
            data=profile_data
        )

    # Interaction Recording API

    def record_interaction(
        self,
        user_id: int,
        course_key: str,
        usage_key: str,
        interaction_type: str,
        data: Dict
    ) -> Dict:
        """
        Record a student interaction for analysis.

        Args:
            user_id: Student user ID
            course_key: Course identifier
            usage_key: XBlock identifier
            interaction_type: Type of interaction
            data: Interaction data

        Returns:
            Analysis results from AI Engine
        """
        payload = {
            'user_id': user_id,
            'course_key': course_key,
            'usage_key': usage_key,
            'interaction_type': interaction_type,
            'data': data
        }
        return self._make_request('POST', '/api/v1/interactions/record', data=payload)

    # Adaptive Feedback API

    def get_adaptive_feedback(
        self,
        user_id: int,
        course_key: str,
        usage_key: str,
        question: Dict,
        answer: Dict
    ) -> Dict:
        """
        Get personalized feedback for a student's answer.

        Args:
            user_id: Student user ID
            course_key: Course identifier
            usage_key: XBlock identifier
            question: Question data
            answer: Student's answer data

        Returns:
            Personalized feedback and adaptation instructions
        """
        data = {
            'user_id': user_id,
            'course_key': course_key,
            'usage_key': usage_key,
            'question': question,
            'answer': answer
        }
        return self._make_request('POST', '/api/v1/adaptation/feedback', data=data)

    # AI Tutor API

    def get_tutor_response(
        self,
        user_id: int,
        course_key: str,
        usage_key: str,
        message: str,
        history: List[Dict]
    ) -> Dict:
        """
        Get AI tutor response to student message.

        Args:
            user_id: Student user ID
            course_key: Course identifier
            usage_key: XBlock identifier
            message: Student's message
            history: Conversation history

        Returns:
            AI tutor response
        """
        data = {
            'user_id': user_id,
            'course_key': course_key,
            'usage_key': usage_key,
            'message': message,
            'history': history
        }
        return self._make_request('POST', '/api/v1/tutor/chat', data=data)

    # Health Check

    def health_check(self) -> Dict:
        """Check if AI Engine is healthy and accessible."""
        try:
            return self._make_request('GET', '/api/v1/health')
        except AIEngineClientError as e:
            log.warning(f"AI Engine health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}
