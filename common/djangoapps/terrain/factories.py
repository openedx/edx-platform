'''
Factories are defined in other modules and absorbed here into the
lettuce world so that they can be used by both unit tests
and integration / BDD tests.
'''
import student.tests.factories as sf
import xmodule.modulestore.tests.factories as xf
import course_modes.tests.factories as cmf
from lettuce import world

# Unlock XBlock factories, because we're randomizing the collection
# name above to prevent collisions
xf.XMODULE_FACTORY_LOCK.enable()

world.absorb(sf.UserFactory)
world.absorb(sf.UserProfileFactory)
world.absorb(sf.RegistrationFactory)
world.absorb(sf.GroupFactory)
world.absorb(sf.CourseEnrollmentAllowedFactory)
world.absorb(cmf.CourseModeFactory)
world.absorb(xf.CourseFactory)
world.absorb(xf.ItemFactory)
