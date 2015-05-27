from factory.django import DjangoModelFactory

from certificates.models import GeneratedCertificate, CertificateStatuses, CertificateHtmlViewConfiguration


# Factories are self documenting
# pylint: disable=missing-docstring
class GeneratedCertificateFactory(DjangoModelFactory):

    FACTORY_FOR = GeneratedCertificate

    course_id = None
    status = CertificateStatuses.unavailable
    mode = GeneratedCertificate.MODES.honor
    name = ''


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
