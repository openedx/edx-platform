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
                "accomplishment_class_append": "accomplishment--certificate--honorcode",
                "certificate_verify_url_prefix": "https://verify-test.edx.org/cert/",
                "certificate_verify_url_suffix": "/verify.html",
                "company_about_url": "http://www.edx.org/about-us",
                "company_courselist_url": "http://www.edx.org/course-list",
                "company_careers_url": "http://www.edx.org/jobs",
                "company_contact_url": "http://www.edx.org/contact-us",
                "platform_name": "edX",
                "company_privacy_url": "http://www.edx.org/edx-privacy-policy",
                "company_tos_url": "http://www.edx.org/edx-terms-service",
                "company_verified_certificate_url": "http://www.edx.org/verified-certificate",
                "document_script_src_modernizr": "https://verify-test.edx.org/v2/static/js/vendor/modernizr-2.6.2.min.js",
                "document_stylesheet_url_normalize": "https://verify-test.edx.org/v2/static/css/vendor/normalize.css",
                "document_stylesheet_url_fontawesome": "https://verify-test.edx.org/v2/static/css/vendor/font-awesome.css",
                "document_stylesheet_url_application": "https://verify-test.edx.org/v2/static/css/style-application.css",
                "logo_src": "https://verify-test.edx.org/v2/static/images/logo-edx.svg",
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
                "document_body_class_append": "is-xseries",
                "document_script_src_modernizr": "https://verify-test.edx.org/xseries/static/js/vendor/modernizr-2.6.2.min.js",
                "document_stylesheet_url_normalize": "https://verify-test.edx.org/xseries/static/css/vendor/normalize.css",
                "document_stylesheet_url_fontawesome": "https://verify-test.edx.org/xseries/static/css/vendor/font-awesome.css",
                "document_stylesheet_url_application": "https://verify-test.edx.org/xseries/static/css/style-application.css",
                "logo_src": "https://verify-test.edx.org/xseries/static/images/logo-edx.svg"
            }
        }"""
