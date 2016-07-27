"""
Course License test factories.
"""
import factory
from factory.django import DjangoModelFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from ccx_keys.locator import CCXLocator

from labster_course_license.models import CourseLicense


class CourseLicenseFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseLicense

    course_id = CCXLocator(org='edX', course='toy', run='2012_Fall', ccx=0)
    license_code = factory.Sequence(u'license{0}'.format)
