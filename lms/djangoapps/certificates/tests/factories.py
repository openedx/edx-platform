from factory.django import DjangoModelFactory

from certificates.models import GeneratedCertificate, CertificateStatuses


# Factories are self documenting
# pylint: disable=missing-docstring
class GeneratedCertificateFactory(DjangoModelFactory):

    FACTORY_FOR = GeneratedCertificate

    course_id = None
    status = CertificateStatuses.unavailable
    mode = GeneratedCertificate.MODES.honor
    name = ''
