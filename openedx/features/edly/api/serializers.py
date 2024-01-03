"""
Serializers for edly_api
"""
import json

from rest_framework import serializers

from openedx.features.edly.models import EdlyMultiSiteAccess
from openedx.features.edly.utils import get_marketing_link


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
            mobile_app_config = self.context['site_configuration'].get('MOBILE_APP_CONFIG', {})
            url = self.context['site_configuration'].get('SITE_NAME', '')
            protocol = 'https' if self.context['request'].is_secure() else 'http'
            mobile_app_config['API_HOST_URL'] = '{}://{}'.format(protocol, url) if url else ''
            mobile_app_config['ORGANIZATION_CODE'] = self.context[
                'edly_sub_org_of_user'].get_edx_organizations
            return str(json.dumps(mobile_app_config))

    def get_site_data(self, obj):  # pylint: disable=unused-argument
        """
        Returns site relevant data from site configuration
        """
        site_data = self.context['site_configuration'].get('BRANDING', {}).copy()
        site_data.update(self.context['site_configuration'].get('COLORS', {}))
        site_data['display_name'] = self.context['edly_sub_org_of_user'].lms_site.name
        site_data['contact_email'] = self.context['site_configuration'].get('contact_email', '')
        marketing_urls = self.context['site_configuration'].get('MKTG_URLS', {})
        site_data['site_url'] = marketing_urls.get('ROOT')
        site_data['tos'] = get_marketing_link(marketing_urls, 'TOS')
        site_data['honor'] = get_marketing_link(marketing_urls, 'HONOR')
        site_data['privacy'] = get_marketing_link(marketing_urls, 'PRIVACY')
        return site_data

    def get_mobile_enabled(self, obj):  # pylint: disable=unused-argument
        """
        Returns mobile_enabled flag
        """
        return self.context['site_configuration'].get('MOBILE_ENABLED', False)


class MutiSiteAccessSerializer(serializers.ModelSerializer):
    """
    Serializer for Mutisite access endpoint
    """
    
    name = serializers.CharField(source='sub_org.name', read_only=True)
    slug = serializers.CharField(source='sub_org.slug', read_only=True)

    class Meta:
        """
        Meta attribute for the MutiSiteAccess Model
        """
        model = EdlyMultiSiteAccess
        fields = ['id', 'name', 'slug']
