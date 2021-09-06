import factory
from factory.django import DjangoModelFactory

from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.models import CertificateGenerationCourseSetting


class CertificateGenerationCourseSettingFactory(DjangoModelFactory):
    class Meta:
        model = CertificateGenerationCourseSetting

    course_key = factory.Sequence(lambda n: CourseKey.from_string(
        'course-v1:HumbleBumble+HB{}+1901'.format(n)))
