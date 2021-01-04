# Factories are self documenting


from uuid import uuid4

from factory.django import DjangoModelFactory

from lms.djangoapps.certificates.models import (
    CertificateHtmlViewConfiguration,
    CertificateInvalidation,
    CertificateStatuses,
    CertificateWhitelist,
    GeneratedCertificate
)
from common.djangoapps.student.models import LinkedInAddToProfileConfiguration


class GeneratedCertificateFactory(DjangoModelFactory):

    class Meta(object):
        model = GeneratedCertificate

    course_id = None
    status = CertificateStatuses.unavailable
    mode = GeneratedCertificate.MODES.honor
    name = ''
    verify_uuid = uuid4().hex
    grade = ''


class CertificateWhitelistFactory(DjangoModelFactory):

    class Meta(object):
        model = CertificateWhitelist

    course_id = None
    whitelist = True
    notes = 'Test Notes'


class CertificateInvalidationFactory(DjangoModelFactory):

    class Meta(object):
        model = CertificateInvalidation

    notes = 'Test Notes'
    active = True


class CertificateHtmlViewConfigurationFactory(DjangoModelFactory):

    class Meta(object):
        model = CertificateHtmlViewConfiguration

    enabled = True
    configuration = """{
            "default": {
                "accomplishment_class_append": "accomplishment-certificate",
                "platform_name": "edX",
                "company_about_url": "http://www.edx.org/about-us",
                "company_privacy_url": "http://www.edx.org/edx-privacy-policy",
                "company_tos_url": "http://www.edx.org/edx-terms-service",
                "company_verified_certificate_url": "http://www.edx.org/verified-certificate",
                "document_stylesheet_url_application": "/static/certificates/sass/main-ltr.css",
                "logo_src": "/static/certificates/images/logo-edx.png",
                "logo_url": "http://www.edx.org"
            },
            "honor": {
                "certificate_type": "Honor Code",
                "certificate_title": "Certificate of Achievement",
                "logo_url": "http://www.edx.org/honor_logo.png"
            },
            "verified": {
                "certificate_type": "Verified",
                "certificate_title": "Verified Certificate of Achievement"
            },
            "xseries": {
                "certificate_title": "XSeries Certificate of Achievement",
                "certificate_type": "XSeries"
            }
        }"""


class LinkedInAddToProfileConfigurationFactory(DjangoModelFactory):

    class Meta(object):
        model = LinkedInAddToProfileConfiguration

    enabled = True
    company_identifier = "1337"
