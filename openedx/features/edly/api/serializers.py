from rest_framework import serializers

from openedx.core.djangoapps.site_configuration.helpers import get_value_for_org


class UserSiteSerializer(serializers.Serializer):
    app_config = serializers.SerializerMethodField()
    site_data = serializers.SerializerMethodField()

    def get_app_config(self, obj):
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
        return mobile_app_config

    def get_site_data(self, obj):
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
        return site_data
