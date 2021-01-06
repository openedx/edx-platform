"""
Serializers for edly_api
"""
import json

from rest_framework import serializers

from edxmako.shortcuts import marketing_link

from openedx.core.djangoapps.site_configuration.helpers import get_value_for_org


class UserSiteSerializer(serializers.Serializer):
    """
    Serializer for user_sites endpoint
    """
    app_config = serializers.SerializerMethodField()
    site_data = serializers.SerializerMethodField()
    mobile_enabled = serializers.SerializerMethodField()

    def get_app_config(self, obj):
        """
        Returns mobile specific data of a site using site configuration
        """
        if self.get_mobile_enabled(obj):
            mobile_app_config = get_value_for_org(
                self.context['edly_sub_org_of_user'].edx_organization.short_name,
                'MOBILE_APP_CONFIG',
                default={}
            )
            url = get_value_for_org(
                self.context['edly_sub_org_of_user'].edx_organization.short_name,
                'SITE_NAME',
                default=''
            )
            protocol = 'https' if self.context['request'].is_secure() else 'http'
            mobile_app_config['API_HOST_URL'] = '{}://{}'.format(protocol, url) if url else ''
            mobile_app_config['ORGANIZATION_CODE'] = self.context['edly_sub_org_of_user'].edx_organization.short_name
            return str(json.dumps(mobile_app_config))

    def get_site_data(self, obj):  # pylint: disable=unused-argument
        """
        Returns site relevant data from site configuration
        """
        site_data = get_value_for_org(
            self.context['edly_sub_org_of_user'].edx_organization.short_name,
            'BRANDING',
            default={}
        )
        site_data.update(
            get_value_for_org(
                self.context['edly_sub_org_of_user'].edx_organization.short_name,
                'COLORS',
                default={}
            )
        )
        site_data['display_name'] = self.context['edly_sub_org_of_user'].lms_site.name
        url = get_value_for_org(
            self.context['edly_sub_org_of_user'].edx_organization.short_name,
            'SITE_NAME',
            default=''
        )
        protocol = 'https' if self.context['request'].is_secure() else 'http'
        site_data['site_url'] = '{}://{}'.format(protocol, url) if url else ''
        site_data['contact_email'] = get_value_for_org(
            self.context['edly_sub_org_of_user'].edx_organization.short_name,
            'contact_email',
            default=''
        )
        site_data['tos'] = marketing_link('TOS')
        site_data['honor'] = marketing_link('HONOR')
        site_data['privacy'] = marketing_link('PRIVACY')
        return site_data

    def get_mobile_enabled(self, obj):  # pylint: disable=unused-argument
        """
        Returns mobile_enabled flag
        """
        mobile_enabled = get_value_for_org(
            self.context['edly_sub_org_of_user'].edx_organization.short_name,
            'MOBILE_ENABLED',
            default=False
        )
        return mobile_enabled
