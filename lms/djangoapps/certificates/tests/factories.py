# Factories are self documenting
# pylint: disable=missing-docstring
from factory.django import DjangoModelFactory, ImageField

from certificates.models import (
    GeneratedCertificate, CertificateStatuses, CertificateHtmlViewConfiguration, CertificateWhitelist, BadgeAssertion,
    BadgeImageConfiguration,
)


class GeneratedCertificateFactory(DjangoModelFactory):

    FACTORY_FOR = GeneratedCertificate

    course_id = None
    status = CertificateStatuses.unavailable
    mode = GeneratedCertificate.MODES.honor
    name = ''


class CertificateWhitelistFactory(DjangoModelFactory):

    FACTORY_FOR = CertificateWhitelist

    course_id = None
    whitelist = True


class BadgeAssertionFactory(DjangoModelFactory):
    FACTORY_FOR = BadgeAssertion

    mode = 'honor'


class BadgeImageConfigurationFactory(DjangoModelFactory):

    FACTORY_FOR = BadgeImageConfiguration

    mode = 'honor'
    icon = ImageField(color='blue', height=50, width=50, filename='test.png', format='PNG')


class CertificateHtmlViewConfigurationFactory(DjangoModelFactory):

    FACTORY_FOR = CertificateHtmlViewConfiguration

    enabled = True
    configuration = """{
            "default": {
                "accomplishment_class_append": "accomplishment-certificate",
                "platform_name": "edX",
                "company_privacy_url": "http://www.edx.org/edx-privacy-policy",
                "company_tos_url": "http://www.edx.org/edx-terms-service",
                "company_verified_certificate_url": "http://www.edx.org/verified-certificate",
                "document_stylesheet_url_application": "/static/certificates/sass/main-ltr.css",
                "logo_src": "/static/certificates/images/logo-edx.svg",
                "logo_url": "http://www.edx.org"
            },
            "honor": {
                "certificate_type": "Honor Code",
                "document_body_class_append": "is-honorcode"
            },
            "verified": {
                "certificate_type": "Verified",
                "document_body_class_append": "is-idverified"
            },
            "xseries": {
                "certificate_type": "XSeries",
                "document_body_class_append": "is-xseries"
            }
        }"""
