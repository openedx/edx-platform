"""
Serializers for course live views.
"""
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from lti_consumer.models import LtiConfiguration
from rest_framework import serializers

from .models import AVAILABLE_PROVIDERS, CourseLiveConfiguration
from .utils import provider_requires_custom_email


class LtiSerializer(serializers.ModelSerializer):
    """
    Serialize LtiConfiguration responses
    """
    lti_config = serializers.JSONField()

    class Meta:
        model = LtiConfiguration
        fields = [
            'lti_1p1_client_key',
            'lti_1p1_client_secret',
            'lti_1p1_launch_url',
            'version',
            'lti_config'
        ]
        read_only = [
            'version'
        ]

    def validate_lti_config(self, value):
        """
        Validates if lti_config contains all required data i.e. custom_instructor_email
        """
        additional_parameters = value.get('additional_parameters', None)
        custom_instructor_email = additional_parameters.get('custom_instructor_email', None)
        requires_email = provider_requires_custom_email(self.context.get('provider_type', ''))

        if additional_parameters and custom_instructor_email and requires_email:
            try:
                validate_email(custom_instructor_email)
            except ValidationError as error:
                raise serializers.ValidationError(f'{custom_instructor_email} is not valid email address') from error
            return value

        if not requires_email:
            return value

        raise serializers.ValidationError('custom_instructor_email is required value in additional_parameters')

    def create(self, validated_data):
        lti_config = validated_data.pop('lti_config', None)
        instance = LtiConfiguration()
        instance.version = 'lti_1p1'
        instance.config_store = LtiConfiguration.CONFIG_ON_DB

        for key, value in validated_data.items():
            if key in set(self.Meta.fields).difference(self.Meta.read_only):
                setattr(instance, key, value)

        share_email, share_username = self.pii_sharing_allowed()
        instance.lti_config = {
            "pii_share_username": share_username,
            "pii_share_email": share_email,
            "additional_parameters": lti_config['additional_parameters']
        }
        instance.save()
        return instance

    def update(self, instance: LtiConfiguration, validated_data: dict) -> LtiConfiguration:
        """
        Create/update a model-backed instance
        """
        instance.config_store = LtiConfiguration.CONFIG_ON_DB
        lti_config = validated_data.pop('lti_config', None)
        if lti_config.get('additional_parameters', None):
            instance.lti_config['additional_parameters'] = lti_config.get('additional_parameters')

        if validated_data:
            for key, value in validated_data.items():
                if key in self.Meta.fields:
                    setattr(instance, key, value)

            share_email, share_username = self.pii_sharing_allowed()
            instance.pii_share_username = share_username
            instance.pii_share_email = share_email
            instance.save()
        return instance

    def pii_sharing_allowed(self):
        """
        Check if email and username sharing is required and allowed
        """
        pii_sharing_allowed = self.context.get('pii_sharing_allowed', False)
        provider = AVAILABLE_PROVIDERS.get(self.context.get('provider_type', None))

        email = pii_sharing_allowed and provider['pii_sharing']['email'] if provider else False
        username = pii_sharing_allowed and provider['pii_sharing']['username'] if provider else False

        return email, username


class CourseLiveConfigurationSerializer(serializers.ModelSerializer):
    """
    Serialize configuration responses
    """
    lti_configuration = LtiSerializer(many=False, read_only=False)
    pii_sharing_allowed = serializers.SerializerMethodField()

    class Meta:
        model = CourseLiveConfiguration

        fields = ['course_key', 'provider_type', 'enabled', 'lti_configuration', 'pii_sharing_allowed']
        read_only_fields = ['course_key']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.context['provider_type'] = self.initial_data.get('provider_type', '')
        except AttributeError:
            self.context['provider_type'] = self.data.get('provider_type', '')

    def get_pii_sharing_allowed(self, instance):
        return self.context['pii_sharing_allowed']

    def to_representation(self, instance):
        payload = super().to_representation(instance)
        if not payload['lti_configuration']:
            payload['lti_configuration'] = LtiSerializer(LtiConfiguration()).data
        return payload

    def create(self, validated_data):
        """
        Create a new CourseLiveConfiguration entry in model
        """
        lti_config = validated_data.pop('lti_configuration')
        instance = CourseLiveConfiguration()
        instance = self._update_course_live_instance(instance, validated_data)
        instance = self._update_lti(instance, lti_config)
        instance.save()
        return instance

    def update(self, instance: CourseLiveConfiguration, validated_data: dict) -> CourseLiveConfiguration:
        """
        Update and save an existing instance
        """
        lti_config = validated_data.pop('lti_configuration')
        instance = self._update_course_live_instance(instance, validated_data)
        instance = self._update_lti(instance, lti_config)
        instance.save()
        return instance

    def _update_course_live_instance(self, instance: CourseLiveConfiguration, data: dict) -> CourseLiveConfiguration:
        """
        Adds data to courseLiveConfiguration model instance
        """
        instance.course_key = self.context.get('course_id')
        instance.enabled = self.validated_data.get('enabled', False)

        if data.get('provider_type') in AVAILABLE_PROVIDERS:
            instance.provider_type = data.get('provider_type')
        else:
            raise serializers.ValidationError(
                f'Provider type {data.get("provider_type")} does not exist')
        return instance

    def _update_lti(
        self,
        instance: CourseLiveConfiguration,
        lti_config: dict,
    ) -> CourseLiveConfiguration:
        """
        Update LtiConfiguration
        """
        lti_serializer = LtiSerializer(
            instance.lti_configuration or None,
            data=lti_config,
            partial=True,
            context={
                'pii_sharing_allowed': self.context.get('pii_sharing_allowed', False),
                'provider_type': self.context.get('provider_type', ''),
            }
        )
        if lti_serializer.is_valid(raise_exception=True):
            lti_serializer.save()
        instance.lti_configuration = lti_serializer.instance
        return instance
