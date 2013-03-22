from lettuce import world, step
from nose.tools import assert_equals, assert_in
from lettuce.django import django_url
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from xmodule.modulestore import Location
from xmodule.modulestore.django import _MODULESTORES, modulestore
from xmodule.templates import update_templates

from logging import getLogger
logger = getLogger(__name__)

TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'Test Course'
TEST_SECTION_NAME = "Problem"


@step(u'The course "([^"]*)" exists$')
def create_course(step, course):

    # First clear the modulestore so we don't try to recreate
    # the same course twice
    # This also ensures that the necessary templates are loaded
    flush_xmodule_store()

    # Create the course
    # We always use the same org and display name,
    # but vary the course identifier (e.g. 600x or 191x)
    course = world.CourseFactory.create(org=TEST_COURSE_ORG,
                                        number=course,
                                        display_name=TEST_COURSE_NAME)

    # Add a section to the course to contain problems
    section = world.ItemFactory.create(parent_location=course.location,
                                       display_name=TEST_SECTION_NAME)

    problem_section = world.ItemFactory.create(parent_location=section.location,
                                               template='i4x://edx/templates/sequential/Empty',
                                               display_name=TEST_SECTION_NAME)


@step(u'I am registered for the course "([^"]*)"$')
def i_am_registered_for_the_course(step, course):
    # Create the course
    create_course(step, course)

    # Create the user
    world.create_user('robot')
    u = User.objects.get(username='robot')

    # If the user is not already enrolled, enroll the user.
    # TODO: change to factory
    CourseEnrollment.objects.get_or_create(user=u, course_id=course_id(course))

    world.log_in('robot', 'test')


@step(u'The course "([^"]*)" has extra tab "([^"]*)"$')
def add_tab_to_course(step, course, extra_tab_name):
    section_item = world.ItemFactory.create(parent_location=course_location(course),
                                            template="i4x://edx/templates/static_tab/Empty",
                                            display_name=str(extra_tab_name))


def flush_xmodule_store():
    # Flush and initialize the module store
    # It needs the templates because it creates new records
    # by cloning from the template.
    # Note that if your test module gets in some weird state
    # (though it shouldn't), do this manually
    # from the bash shell to drop it:
    # $ mongo test_xmodule --eval "db.dropDatabase()"
    _MODULESTORES = {}
    modulestore().collection.drop()
    update_templates()


def course_id(course_num):
    return "%s/%s/%s" % (TEST_COURSE_ORG, course_num,
                         TEST_COURSE_NAME.replace(" ", "_"))


def course_location(course_num):
    return Location(loc_or_tag="i4x",
                    org=TEST_COURSE_ORG,
                    course=course_num,
                    category='course',
                    name=TEST_COURSE_NAME.replace(" ", "_"))


def section_location(course_num):
    return Location(loc_or_tag="i4x",
                    org=TEST_COURSE_ORG,
                    course=course_num,
                    category='sequential',
                    name=TEST_SECTION_NAME.replace(" ", "_"))
