"""
Services for AI Translations.
"""

from hashlib import sha256
import json

from django.conf import settings
from edx_rest_api_client.client import OAuthAPIClient


class AiTranslationService:
    """
    A service which communicates with ai-translations for translation-related tasks
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Client for communicating with ai-translations, singleton creation."""
        if not self._client:
            self._client = self._init_translations_client()
        return self._client

    def _init_translations_client(self):
        """Initialize OAuth connection to ai-translations"""
        return OAuthAPIClient(
            base_url=settings.TRANSLATIONS_SERVICE_EDX_OAUTH2_PROVIDER_URL,
            client_id=settings.TRANSLATIONS_SERVICE_EDX_OAUTH2_KEY,
            client_secret=settings.TRANSLATIONS_SERVICE_EDX_OAUTH2_SECRET,
        )

    def translate(self, content, language, block_id):
        """Request translated version of content from translations IDA"""

        url = f"{settings.AI_TRANSLATIONS_API_URL}/translate-xblock/"
        headers = {
            "content-type": "application/json",
            "use-jwt-cookie": "true",
        }
        payload = {
            "block_id": str(block_id),
            "source_language": "en",
            "target_language": language,
            "content": content,
            "content_hash": sha256(content.encode("utf-8")).hexdigest(),
        }

        response = self.client.post(url, data=json.dumps(payload), headers=headers)

        return response.json().get("translated_content")
