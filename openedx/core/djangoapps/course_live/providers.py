from abc import ABC
from typing import List, Dict
from django.conf import settings


class LiveProvider(ABC):
    id: str
    name: str
    features: List[str] = []
    requires_username: bool = False
    requires_email: bool = False
    additional_parameters: List[str] = []
    has_free_tier: bool = False

    def requires_pii_sharing(self):
        """
        Check if provider requires any PII ie username or email
        """
        return self.requires_email or self.requires_username

    def requires_custom_email(self):
        """
        Check if provider requires custom instructor email
        """
        return 'custom_instructor_email' in self.additional_parameters

    def is_enabled(self):
        raise NotImplementedError()


class Zoom(LiveProvider):
    id = 'zoom'
    name = 'Zoom LTI PRO'
    additional_parameters = [
        'custom_instructor_email'
    ]

    @property
    def is_enabled(self):
        return True


class BigBlueButton(LiveProvider):
    id = 'big_blue_button'
    name = 'Big Blue Button'
    requires_username: bool = True

    @property
    def has_free_tier(self) -> bool:
        """
        Check if free tier is enabled by checking for valid keys
        """
        return self._has_valid_global_keys()

    @property
    def is_enabled(self) -> bool:
        return True

    @staticmethod
    def _get_global_keys() -> Dict:
        """
        Get keys from settings
        """
        breakpoint()
        try:
            return settings.COURSE_LIVE_GLOBAL_CREDENTIALS.get('BIG_BLUE_BUTTON', {})
        except AttributeError:
            return {}

    def _has_valid_global_keys(self) -> bool:
        """
        Check if keys are valid and not None
        """
        key = self._get_global_keys()
        if key:
            return bool(key.get("KEY", None) and key.get("SECRET", None) and key.get("URL", None))
        return False


class ProviderManager:
    providers: Dict[str, LiveProvider]

    def __init__(self):
        # auto detect live providers.
        self.providers = {provider.id: provider() for provider in LiveProvider.__subclasses__()}

    def get_enabled_providers(self) -> Dict[str, LiveProvider]:
        """
        Get Enabled providers
        """
        return {key: provider for (key, provider) in self.providers.items() if provider.is_enabled}
