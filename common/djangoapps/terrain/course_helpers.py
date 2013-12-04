# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world
from django.contrib.auth.models import User, Group
from student.models import CourseEnrollment
from xmodule.modulestore.django import editable_modulestore
from xmodule.contentstore.django import contentstore


@world.absorb
def create_user(uname, password):

    # If the user already exists, don't try to create it again
    if len(User.objects.filter(username=uname)) > 0:
        return

    portal_user = world.UserFactory.build(username=uname, email=uname + '@edx.org')
    portal_user.set_password(password)
    portal_user.save()

    registration = world.RegistrationFactory(user=portal_user)
    registration.register(portal_user)
    registration.activate()

    world.UserProfileFactory(user=portal_user)


@world.absorb
def log_in(username='robot', password='test', email='robot@edx.org', name='Robot'):
    """
    Use the auto_auth feature to programmatically log the user in
    """
    url = '/auto_auth?username=%s&password=%s&name=%s&email=%s' % (username,
          password, name, email)
    world.visit(url)

    # Save the user info in the world scenario_dict for use in the tests
    user = User.objects.get(username=username)
    world.scenario_dict['USER'] = user


@world.absorb
def register_by_course_id(course_id, username='robot', password='test', is_staff=False):
    create_user(username, password)
    user = User.objects.get(username=username)
    if is_staff:
        user.is_staff = True
        user.save()
    CourseEnrollment.enroll(user, course_id)


@world.absorb
def add_to_course_staff(username, course_num):
    """
    Add the user with `username` to the course staff group
    for `course_num`.
    """
    # Based on code in lms/djangoapps/courseware/access.py
    group_name = "instructor_{}".format(course_num)
    group, _ = Group.objects.get_or_create(name=group_name)
    group.save()

    user = User.objects.get(username=username)
    user.groups.add(group)


@world.absorb
def clear_courses():
    # Flush and initialize the module store
    # Note that if your test module gets in some weird state
    # (though it shouldn't), do this manually
    # from the bash shell to drop it:
    # $ mongo test_xmodule --eval "db.dropDatabase()"
    editable_modulestore().collection.drop()
    contentstore().fs_files.drop()
    editable_modulestore().metadata_inheritance_cache_subsystem.clear()
    editable_modulestore().metadata_inheritance_cache_subsystem = None