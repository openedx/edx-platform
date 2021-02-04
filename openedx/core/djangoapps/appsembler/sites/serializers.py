import beeline
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import transaction
from rest_framework import serializers
from organizations import api as organizations_api
from organizations.models import Organization

from student.forms import validate_username
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.appsembler.sites.tasks import (
    import_course_on_site_creation_apply_async,
)
from openedx.core.djangoapps.appsembler.sites.models import AlternativeDomain
from openedx.core.djangoapps.appsembler.sites.utils import sass_to_dict, dict_to_sass, bootstrap_site


class SASSDictField(serializers.DictField):
    def to_internal_value(self, data):
        return dict_to_sass(data)

    def to_representation(self, value):
        return sass_to_dict(value)


class SiteConfigurationSerializer(serializers.ModelSerializer):
    values = serializers.DictField()
    sassVariables = serializers.ListField(source='sass_variables')
    pageElements = serializers.DictField(source='page_elements')

    class Meta:
        model = SiteConfiguration
        fields = ('id', 'values', 'sassVariables', 'pageElements')

    @beeline.traced(name="SiteConfigurationSerializer.update")
    def update(self, instance, validated_data):
        beeline.add_context_field("validated_data", validated_data)
        object = super(SiteConfigurationSerializer, self).update(instance, validated_data)
        return object


class SiteConfigurationListSerializer(SiteConfigurationSerializer):
    class Meta(SiteConfigurationSerializer.Meta):
        fields = ('id', 'name', 'domain')


class AlternativeDomainSerializer(serializers.ModelSerializer):
    site = serializers.PrimaryKeyRelatedField(queryset=Site.objects.all())

    class Meta:
        model = AlternativeDomain
        fields = ('id', 'site', 'domain')

    @beeline.traced(name="AlternativeDomainSerializer.create")
    def create(self, validated_data):
        """
        Allow only one alternative domain per Site model.
        """
        beeline.add_context_field("validated_data", validated_data)
        domain, created = AlternativeDomain.objects.get_or_create(
            site=validated_data.get('site', None),
            defaults={'domain': validated_data.get('domain', None)})
        beeline.add_context_field("domain", domain)
        beeline.add_context_field("created", created)
        if not created:
            domain.domain = validated_data.get('domain', None)
            domain.save()
        return domain


class SiteSerializer(serializers.ModelSerializer):
    configuration = SiteConfigurationSerializer(read_only=True)
    alternativeDomain = AlternativeDomainSerializer(source='alternative_domain', read_only=True)
    customDomainStatus = serializers.SerializerMethodField('custom_domain_status', read_only=True)

    class Meta:
        model = Site
        fields = ('id', 'name', 'domain', 'configuration', 'alternativeDomain', 'customDomainStatus')

    @beeline.traced(name="SiteSerializer.create")
    def create(self, validated_data):
        beeline.add_context_field("validated_data", validated_data)
        site = super(SiteSerializer, self).create(validated_data)
        organization, site, user = bootstrap_site(site)
        return site

    @beeline.traced(name="SiteSerializer.custom_domain_status")
    def custom_domain_status(self, obj):
        if not hasattr(obj, 'alternative_domain'):
            return 'inactive'
        return 'active' if obj.alternative_domain.is_tahoe_domain() else 'inactive'


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'short_name', 'edx_uuid')

    @beeline.traced(name="OrganizationSerializer.create")
    def create(self, validated_data):
        beeline.add_context_field("validated_data", validated_data)
        return organizations_api.add_organization(**validated_data)


class RegistrationSerializer(serializers.Serializer):
    site = SiteSerializer()
    organization = OrganizationSerializer()
    username = serializers.CharField(required=False, validators=[validate_username])
    user_email = serializers.EmailField(required=False)  # TODO: Remove after all MTE work is done.
    password = serializers.CharField(required=False)
    initial_values = serializers.DictField(required=False)

    @beeline.traced(name="RegistrationSerializer.create")
    def create(self, validated_data):
        beeline.add_context_field('validated_data', validated_data)
        site_data = validated_data.pop('site')
        site = Site.objects.create(**site_data)
        organization_data = validated_data.pop('organization')
        username = validated_data.pop('username', None)
        organization, site, user = bootstrap_site(site, organization_data, username)
        site_configuration = site.configuration
        initial_values = validated_data.get('initial_values', {})
        if initial_values:
            site_configuration.values['SITE_NAME'] = site.domain
            site_configuration.values['platform_name'] = initial_values.get('platform_name')
            site_configuration.values['logo_positive'] = initial_values.get('logo_positive')
            site_configuration.values['logo_negative'] = initial_values.get('logo_negative')
            site_configuration.values['primary-font'] = initial_values.get('font')
            site_configuration.values['accent-font'] = 'Delius Unicase'
            site_configuration.values['page_status'] = {
                'about': True,
                'blog': True,
                'contact': True,
                'copyright': True,
                'donate': False,
                'embargo': False,
                'faq': True,
                'help': True,
                'honor': True,
                'jobs': False,
                'news': True,
                'press': True,
                'privacy': True,
                'tos': True
            }
            site_configuration.set_sass_variables({
                '$brand-primary-color': initial_values.get('primary_brand_color'),
                '$base-text-color': initial_values.get('base_text_color'),
                '$cta-button-bg': initial_values.get('cta_button_bg'),
                '$primary-font-name': '"{}"'.format(initial_values.get('font')),
                '$accent-font-name': '"Delius Unicase"',
            })
            site_configuration.save()

        # clone course
        if settings.FEATURES.get("APPSEMBLER_IMPORT_DEFAULT_COURSE_ON_SITE_CREATION", False):
            beeline.add_context_field("default_course_on_site_creation_flag", True)

            def import_task_on_commit():
                """
                Run the import task after the commit to avoid Organization.DoesNotExist error on the Celery.
                """
                import_course_on_site_creation_apply_async(organization)
            transaction.on_commit(import_task_on_commit)

        return {
            'site': site,
            'organization': organization,
            'password': 'hashed',
            'initial_values': initial_values,
        }
