""" Management command to set up Edly Multisite Devstack locally """

import csv

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import connection
from oauth2_provider.models import Application
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.models import SiteTheme
from openedx.features.edly.models import EdlyOrganization, EdlySubOrganization
from organizations.models import Organization
from waffle.models import Switch


class Command(BaseCommand):
    """Command to Set up LMS & Studio Site Locally."""
    lms_domain_name = "edx.devstack.lms:18000"
    studio_domain_name = "edx.devstack.lms:18010"

    def setup_lms_and_studio_site(self):
        """Set up LMS & Studio Site Locally."""
        lms_site, _ = Site.objects.get_or_create(name=self.lms_domain_name, domain=self.lms_domain_name)
        studio_site, _ = Site.objects.get_or_create(name=self.studio_domain_name, domain=self.studio_domain_name)

        SiteTheme.objects.get_or_create(site=lms_site, theme_dir_name='st-lutherx')
        SiteTheme.objects.get_or_create(site=studio_site, theme_dir_name='st-lutherx')

        SiteConfiguration.objects.get_or_create(site=lms_site, enabled=True, site_values={
            "ENABLE_LEARNER_RECORDS": False,
            "course_org_filter": "edly",
            "enable_forum_notifications": True,
            "SITE_NAME": "edx.devstack.lms:18000",
            "site_domain": "edx.devstack.lms:18000",
            "CREDENTIALS_INTERNAL_SERVICE_URL": "http://edx.devstack.lms:18150",
            "CREDENTIALS_PUBLIC_SERVICE_URL": "http://edx.devstack.lms:18150",
            "MKTG_URLS": {
                "ROOT": "http://wordpress.edx.devstack.lms/",
                "NAV_MENU": "wp-json/edly-wp-routes/nav-menu",
                "FOOTER": "wp-json/edly-wp-routes/footer",
                "COURSES": "/courses"
            },
            "EDLY_COPYRIGHT_TEXT": "Edly Copy Rights. All rights reserved for edly site.",
            "SESSION_COOKIE_DOMAIN": ".edx.devstack.lms",
            "SERVICES_NOTIFICATIONS_COOKIE_EXPIRY": "900",
            "PANEL_NOTIFICATIONS_BASE_URL": "http://panel.edx.devstack.lms:9999/",
            "COLORS": {
                "primary": "#dd1f25",
                "secondary": "#dd1f25"
            },
            "FONTS": {
                "base-font": "Open Sans, sans-serif",
                "heading-font": "Open Sans, sans-serif",
                "font-path": "https://fonts.googleapis.com/css?family=Open+Sans&display=swap"
            },
            "BRANDING": {
                "logo": "https://edly-cloud-static-assets.s3.amazonaws.com/red-theme/logo.png",
                "logo-white": "https://edly-cloud-static-assets.s3.amazonaws.com/red-theme/logo-white.png",
                "favicon": "https://edly-cloud-static-assets.s3.amazonaws.com/red-theme/favicon.png"
            },
            "CONTACT_MAILING_ADDRESS": "Edly 25 Mohlanwal Road, Westwood Colony Lahore, Punjab 54000",
            "email_from_address": "<from email address>",
            "CONTACT_EMAIL": "<Contact email address>",
            "contact_email": "<Contact email address>",
            "COURSE_CATALOG_API_URL": "http://edx.devstack.lms:18381/api/v1",
            "GTM_ID": "GTM-M69F9BL",
            "DJANGO_SETTINGS_OVERRIDE": {
                "CURRENT_PLAN": "ESSENTIALS",
                "CSRF_TRUSTED_ORIGINS": [
                    ".edx.devstack.lms",
                    "panel.edx.devstack.lms:3030"
                ],
                "CORS_ORIGIN_WHITELIST": ["https://apps.edx.devstack.lms:3030"],
                "REGISTRATION_EXTRA_FIELDS": {
                    "phone_number": "hidden",
                    "city": "hidden",
                    "confirm_email": "hidden",
                    "country": "optional",
                    "gender": "optional",
                    "goals": "optional",
                    "honor_code": "required",
                    "level_of_education": "optional",
                    "mailing_address": "hidden",
                    "terms_of_service": "hidden",
                    "year_of_birth": "optional"
                },
                "DEFAULT_FROM_EMAIL": "<from email address>",
                "CREDENTIALS_INTERNAL_SERVICE_URL": "http://edx.devstack.lms:18150",
                "CREDENTIALS_PUBLIC_SERVICE_URL": "http://edx.devstack.lms:18150",
                "BULK_EMAIL_DEFAULT_FROM_EMAIL": "<from email address>",
                "ECOMMERCE_API_URL": "http://edx.devstack.lms:18130/api/v2",
                "FEATURES": {
                    "ENABLE_DISCUSSION_HOME_PANEL": True,
                    "ENABLE_DISCUSSION_SERVICE": True
                },
                "SESSION_COOKIE_DOMAIN": ".edx.devstack.lms",
                "LANGUAGE_CODE": "en",
                "PLATFORM_NAME": "Edly Site",
                "STUDIO_NAME": "Edly Site",
                "CMS_BASE": "edx.devstack.lms:18010",
                "LMS_BASE": "edx.devstack.lms:18000",
                "LOGIN_REDIRECT_WHITELIST": [
                    "edx.devstack.lms:18010"
                ],
                "SITE_NAME": "edx.devstack.lms:18000",
                "LMS_ROOT_URL": "http://edx.devstack.lms:18000",
                "MARKETING_SITE_ROOT": "http://wordpress.edx.devstack.lms/",
                "MKTG_URLS": {
                    "ROOT": "http://wordpress.edx.devstack.lms/",
                    "NAV_MENU": "wp-json/edly-wp-routes/nav-menu",
                    "FOOTER": "wp-json/edly-wp-routes/footer",
                    "COURSES": "/courses"
                },
                "ECOMMERCE_PUBLIC_URL_ROOT": "http://edx.devstack.lms:18130",
                "LMS_SEGMENT_KEY": "",
                "BADGR_ISSUER_SLUG": "",
                "CMS_SEGMENT_KEY": "",
                "BADGR_USERNAME": "",
                "BADGR_PASSWORD": ""
            }
        })
        SiteConfiguration.objects.get_or_create(site=studio_site, enabled=True, site_values={
            "course_org_filter": "edly",
            "EDLY_COPYRIGHT_TEXT": " Edly Copy Rights. All rights reserved for dev site.",
            "SESSION_COOKIE_DOMAIN": ".edx.devstack.lms",
            "SERVICES_NOTIFICATIONS_COOKIE_EXPIRY": "900",
            "PANEL_NOTIFICATIONS_BASE_URL": "http://panel.edx.devstack.lms:9999/",
            "COLORS": {
                "primary": "#dd1f25",
                "secondary": "#dd1f25"
            },
            "FONTS": {
                "base-font": "Open Sans, sans-serif",
                "heading-font": "Open Sans, sans-serif",
                "font-path": "https://fonts.googleapis.com/css?family=Open+Sans&display=swap"
            },
            "BRANDING": {
                "logo": "https://edly-cloud-static-assets.s3.amazonaws.com/red-theme/logo.png",
                "logo-white": "https://edly-cloud-static-assets.s3.amazonaws.com/red-theme/logo-white.png",
                "favicon": "https://edly-cloud-static-assets.s3.amazonaws.com/red-theme/favicon.png"
            },
            "CONTACT_MAILING_ADDRESS": "Edly 25 Mohlanwal Road, Westwood Colony Lahore, Punjab 54000",
            "email_from_address": "<from email address>",
            "GTM_ID": "GTM-M69F9BL",
            "DJANGO_SETTINGS_OVERRIDE": {
                "CURRENT_PLAN": "ESSENTIALS",
                "FRONTEND_LOGIN_URL": "http://edx.devstack.lms:18000/login/",
                "FRONTEND_LOGOUT_URL": "http://edx.devstack.lms:18000/logout/",
                "DEFAULT_FROM_EMAIL": "<from email address>",
                "BULK_EMAIL_DEFAULT_FROM_EMAIL": "<from email address>",
                "LMS_ROOT_URL": "http://edx.devstack.lms:18000",
                "SESSION_COOKIE_DOMAIN": ".edx.devstack.lms",
                "LANGUAGE_CODE": "en",
                "PLATFORM_NAME": "Edly Site",
                "SITE_NAME": "edx.devstack.lms:18000",
                "STUDIO_NAME": "Edly Site",
                "CSRF_TRUSTED_ORIGINS": [
                    ".edx.devstack.lms",
                    "panel.edx.devstack.lms:3030"
                ],
                "CORS_ORIGIN_WHITELIST": [
                    "https://apps.edx.devstack.lms:3030"
                ],
                "CMS_BASE": "edx.devstack.lms:18010",
                "LOGIN_REDIRECT_WHITELIST": [
                    "edx.devstack.lms:18010"
                ],
                "MARKETING_SITE_ROOT": "http://wordpress.edx.devstack.lms/",
                "LMS_BASE": "edx.devstack.lms:18000",
                "FEATURES": {
                    "PREVIEW_LMS_BASE": "edx.devstack.lms:18000"
                },
                "MKTG_URLS": {
                    "ROOT": "http://wordpress.edx.devstack.lms/",
                    "NAV_MENU": "wp-json/edly-wp-routes/nav-menu",
                    "FOOTER": "wp-json/edly-wp-routes/footer"
                },
                "LMS_SEGMENT_KEY": "",
                "BADGR_ISSUER_SLUG": "",
                "CMS_SEGMENT_KEY": "",
                "BADGR_USERNAME": "",
                "BADGR_PASSWORD": ""
            }
        })

        organization, _ = Organization.objects.get_or_create(name='Edly', short_name='edly')
        edly_organization, _ = EdlyOrganization.objects.get_or_create(name='Edly Organization', slug='edly',
                                                                      enable_all_edly_sub_org_login=True)

        edly_suborganization, _ = EdlySubOrganization.objects.get_or_create(
            name='Edly Organization', slug='edly',
            edly_organization=edly_organization,
            edx_organization=organization,
            lms_site=lms_site, studio_site=studio_site,
            preview_site=lms_site
        )

        edly_suborganization.edx_organizations.set([organization])

        Switch.objects.get_or_create(name='DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH', active=True)
        Switch.objects.get_or_create(name='ENABLE_COURSE_PROGRESS_SWICTH', active=True)
        Switch.objects.get_or_create(name='enable_edly_organizations', active=True)
        Switch.objects.get_or_create(name='completion.enable_completion_tracking', active=True)
        Switch.objects.get_or_create(name='ENABLE_NOTIFICATIONS', active=True)
        Switch.objects.get_or_create(name='verify_student_disable_account_activation_requirement', active=True)
        Switch.objects.get_or_create(name='enable_course_progress_feature', active=True)

    @staticmethod
    def update_credentials():
        """Update credentials and redirect uris."""
        Application.objects.filter(name='credentials-sso').update(
            redirect_uris='http://edx.devstack.lms:18150/complete/edx-oauth2/')

        CatalogIntegration.objects.get_or_create(internal_api_url='https://edx.devstack.lms:18381/api', enabled=True)

        CredentialsApiConfig.objects.get_or_create(
            internal_service_url='http://edx.devstack.lms:18150/',
            public_service_url='http://edx.devstack.lms:18150/',
            enable_learner_issuance=True,
            enable_studio_authoring=True,
            enabled=True
        )

        Application.objects.filter(name='ecommerce-sso').update(
            redirect_uris='http://edx.devstack.lms:18130/complete/edx-oauth2/')

    @staticmethod
    def write_user_api_userretirementstatus_to_csv():
        """Write user_api_userretirementstatus to csv file."""
        sql_query = """
        SELECT
        username,
        id as user_id
        FROM auth_user
        WHERE id NOT IN (
            SELECT user_id FROM user_api_userretirementstatus
        )
        UNION SELECT
            original_username AS username,
            user_id
        FROM user_api_userretirementstatus;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()

        csv_file_path = 'users_data.csv'
        with open(csv_file_path, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(results)

    def handle(self, *args, **options):
        """Set up LMS & Studio Site Locally and update credentials."""
        self.setup_lms_and_studio_site()
        self.update_credentials()
        self.write_user_api_userretirementstatus_to_csv()
