"""
Platform 2.0 serializers.
"""

import beeline
from rest_framework import serializers
from django.core import validators

import tahoe_sites.api

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.appsembler.sites import site_config_client_helpers

from .tasks import import_course_on_site_creation_after_transaction


ORG_NAME_REGEX = r'^[a-zA-Z0-9\._-]+$'


class TahoeSiteCreationSerializer(serializers.Serializer):
    """
    Platform 2.0 Tahoe site creation serializer.
    """
    site_uuid = serializers.UUIDField(required=False)
    short_name = serializers.CharField(
        required=True,
        help_text=('Organization and site name. Please do not use spaces or special characters. '
                   'Only allowed special character is hyphen (-).'),
        validators=[
            validators.RegexValidator(regex=ORG_NAME_REGEX),
        ],
    )
    domain = serializers.CharField(
        required=True,
        help_text='Full domain name for the Tahoe site e.g. academy.tahoe.appsembler.com or courses.example.com',
    )

    class Meta:
        fields = ('site_uuid', 'short_name', 'domain',)

    @beeline.traced(name='TahoeSiteCreationSerializer.create')
    def create(self, validated_data):
        # assert False, validated_data
        beeline.add_context_field('validated_data', validated_data)
        created_site_data = tahoe_sites.api.create_tahoe_site(
            domain=validated_data['domain'],
            short_name=validated_data['short_name'],
            uuid=validated_data.get('site_uuid'),
        )

        site = created_site_data['site']
        organization = created_site_data['organization']

        tahoe_custom_site_config_params = {}
        if hasattr(SiteConfiguration, 'sass_variables'):
            # This works SiteConfiguration with and without our custom
            # fields of: sass_variables and page_elements.
            # TODO: Fix Site Configuration hacks: https://github.com/appsembler/edx-platform/issues/329
            tahoe_custom_site_config_params['page_elements'] = {}
            tahoe_custom_site_config_params['sass_variables'] = {}

        site_config = SiteConfiguration.objects.create(
            site=site,
            enabled=True,
            site_values={},  # Empty values. Should use the `site_config_client_helpers` instead this field.
            **tahoe_custom_site_config_params,
        )

        sass_status = site_config.compile_microsite_sass()

        site_config_client_helpers.enable_for_site(
            site=site,
            note='domain = {domain} , organization name = {short_name} -- (system generated note).'.format(
                **validated_data,
            ),
        )
        course_creation_task_scheduled = import_course_on_site_creation_after_transaction(organization)

        return {
            'site_configuration': site_config,
            'course_creation_task_scheduled': course_creation_task_scheduled,
            'site_configuration_client_enabled': True,
            **sass_status,
            **created_site_data,
        }
