from factory.django import DjangoModelFactory

from opaque_keys.edx.locations import SlashSeparatedCourseKey

from certificates.models import GeneratedCertificate, CertificateStatuses, MODES

# Factories don't have __init__ methods, and are self documenting
# pylint: disable=W0232
class GeneratedCertificateFactory(DjangoModelFactory):

    FACTORY_FOR = GeneratedCertificate

    course_id = None
    status = CertificateStatuses.unavailable
    mode = MODES.honor
    name = ''
