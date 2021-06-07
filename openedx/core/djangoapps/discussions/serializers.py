"""
Serializers for Discussion views.
"""

from lti_consumer.models import LtiConfiguration
from rest_framework import serializers

from lms.djangoapps.discussion.rest_api.serializers import DiscussionSettingsSerializer
from openedx.core.djangoapps.django_comment_common.models import CourseDiscussionSettings
from openedx.core.lib.courses import get_course_by_id
from xmodule.modulestore.django import modulestore

from .models import DEFAULT_PROVIDER_TYPE, AVAILABLE_PROVIDER_MAP, DiscussionsConfiguration, Features


class LtiSerializer(serializers.ModelSerializer):
    """
    Serialize LtiConfiguration responses
    """
    class Meta:
        model = LtiConfiguration
        fields = [
            'lti_1p1_client_key',
            'lti_1p1_client_secret',
            'lti_1p1_launch_url',
            'version',
        ]

    def to_internal_value(self, data: dict) -> dict:
        """
        Transform the incoming primitive data into a native value
        """
        data = data or {}
        payload = {
            key: value
            for key, value in data.items()
            if key in self.Meta.fields
        }
        return payload

    def update(self, instance: LtiConfiguration, validated_data: dict) -> LtiConfiguration:
        """
        Create/update a model-backed instance
        """
        instance = instance or LtiConfiguration()
        instance.config_store = LtiConfiguration.CONFIG_ON_DB
        if validated_data:
            for key, value in validated_data.items():
                if key in self.Meta.fields:
                    setattr(instance, key, value)
            instance.save()
        return instance


class LegacySettingsSerializer(serializers.BaseSerializer):
    """
    Serialize legacy discussions settings
    """
    class Meta:
        fields = [
            'allow_anonymous',
            'allow_anonymous_to_peers',
            'discussion_blackouts',
            'discussion_topics',
            # The following fields are deprecated;
            # they technically still exist in Studio (so we mention them here),
            # but they are not supported in the new experience:
            # 'discussion_link',
            # 'discussion_sort_alpha',
        ]
        fields_cohorts = [
            'always_divide_inline_discussions',
            'divided_course_wide_discussions',
            'divided_inline_discussions',
            'division_scheme',
        ]

    def create(self, validated_data):
        """
        We do not need this.
        """
        raise NotImplementedError

    def to_internal_value(self, data: dict) -> dict:
        """
        Transform the incoming primitive data into a native value
        """
        if not isinstance(data.get('allow_anonymous', False), bool):
            raise serializers.ValidationError('Wrong type for allow_anonymous')
        if not isinstance(data.get('allow_anonymous_to_peers', False), bool):
            raise serializers.ValidationError('Wrong type for allow_anonymous_to_peers')
        if not isinstance(data.get('discussion_blackouts', []), list):
            raise serializers.ValidationError('Wrong type for discussion_blackouts')
        if not isinstance(data.get('discussion_topics', {}), dict):
            raise serializers.ValidationError('Wrong type for discussion_topics')
        return data

    def to_representation(self, instance) -> dict:
        """
        Serialize data into a dictionary, to be used as a response
        """
        settings = {
            field.name: field.read_json(instance)
            for field in instance.fields.values()
            if field.name in self.Meta.fields
        }
        discussion_settings = CourseDiscussionSettings.get(instance.id)
        serializer = DiscussionSettingsSerializer(
            discussion_settings,
            context={
                'course': instance,
                'settings': discussion_settings,
            },
            partial=True,
        )
        settings.update({
            key: value
            for key, value in serializer.data.items()
            if key != 'id'
        })
        return settings

    def update(self, instance, validated_data: dict):
        """
        Update and save an existing instance
        """
        save = False
        cohort_settings = {}
        for field, value in validated_data.items():
            if field in self.Meta.fields:
                setattr(instance, field, value)
                save = True
            elif field in self.Meta.fields_cohorts:
                cohort_settings[field] = value
        if cohort_settings:
            discussion_settings = CourseDiscussionSettings.get(instance.id)
            serializer = DiscussionSettingsSerializer(
                discussion_settings,
                context={
                    'course': instance,
                    'settings': discussion_settings,
                },
                data=cohort_settings,
                partial=True,
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
        if save:
            modulestore().update_item(instance, self.context['user_id'])
        return instance


class DiscussionsConfigurationSerializer(serializers.ModelSerializer):
    """
    Serialize configuration responses
    """

    class Meta:
        model = DiscussionsConfiguration
        fields = [
            'enabled',
            'provider_type',
        ]

    def create(self, validated_data):
        """
        We do not need this.
        """
        raise NotImplementedError

    def to_internal_value(self, data: dict) -> dict:
        """
        Transform the *incoming* primitive data into a native value.
        """
        payload = {
            'context_key': data.get('course_key', ''),
            'enabled': data.get('enabled', False),
            'lti_configuration': data.get('lti_configuration', {}),
            'plugin_configuration': data.get('plugin_configuration', {}),
            'provider_type': data.get('provider_type', DEFAULT_PROVIDER_TYPE),
        }
        return payload

    def to_representation(self, instance: DiscussionsConfiguration) -> dict:
        """
        Serialize data into a dictionary, to be used as a response
        """
        payload = super().to_representation(instance)
        lti_configuration_data = {}
        supports_lti = instance.supports('lti')
        if supports_lti:
            lti_configuration = LtiSerializer(instance.lti_configuration)
            lti_configuration_data = lti_configuration.data
        provider_type = instance.provider_type or DEFAULT_PROVIDER_TYPE
        plugin_configuration = instance.plugin_configuration
        if provider_type == 'legacy':
            course_key = instance.context_key
            course = get_course_by_id(course_key)
            legacy_settings = LegacySettingsSerializer(
                course,
                data=plugin_configuration,
            )
            if legacy_settings.is_valid(raise_exception=True):
                plugin_configuration = legacy_settings.data
        features_list = [feature.value for feature in Features]
        payload.update({
            'features': features_list,
            'lti_configuration': lti_configuration_data,
            'plugin_configuration': plugin_configuration,
            'providers': {
                'active': provider_type or DEFAULT_PROVIDER_TYPE,
                'available': AVAILABLE_PROVIDER_MAP,
            },
        })
        return payload

    def update(self, instance: DiscussionsConfiguration, validated_data: dict) -> DiscussionsConfiguration:
        """
        Update and save an existing instance
        """
        for key in self.Meta.fields:
            value = validated_data.get(key)
            if value is not None:
                setattr(instance, key, value)
        # _update_* helpers assume `enabled` and `provider_type`
        # have already been set
        instance = self._update_lti(instance, validated_data)
        instance = self._update_plugin_configuration(instance, validated_data)
        instance.save()
        return instance

    def _update_lti(self, instance: DiscussionsConfiguration, validated_data: dict) -> DiscussionsConfiguration:
        """
        Update LtiConfiguration
        """
        lti_configuration_data = validated_data.get('lti_configuration')
        supports_lti = instance.supports('lti')
        if not supports_lti:
            instance.lti_configuration = None
        elif lti_configuration_data:
            lti_configuration = instance.lti_configuration or LtiConfiguration()
            lti_serializer = LtiSerializer(
                lti_configuration,
                data=lti_configuration_data,
                partial=True,
            )
            if lti_serializer.is_valid(raise_exception=True):
                lti_serializer.save()
            instance.lti_configuration = lti_configuration
        return instance

    def _update_plugin_configuration(
        self,
        instance: DiscussionsConfiguration,
        validated_data: dict,
    ) -> DiscussionsConfiguration:
        """
        Create/update legacy provider settings
        """
        updated_provider_type = validated_data.get('provider_type') or instance.provider_type
        will_support_legacy = bool(
            updated_provider_type == 'legacy'
        )
        if will_support_legacy:
            course_key = instance.context_key
            course = get_course_by_id(course_key)
            legacy_settings = LegacySettingsSerializer(
                course,
                context={
                    'user_id': self.context['user_id'],
                },
                data=validated_data.get('plugin_configuration', {}),
            )
            if legacy_settings.is_valid(raise_exception=True):
                legacy_settings.save()
            instance.plugin_configuration = {}
        else:
            instance.plugin_configuration = validated_data.get('plugin_configuration') or {}
        return instance
