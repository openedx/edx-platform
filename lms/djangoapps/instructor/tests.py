"""
Unit tests for instructor dashboard

Based on (and depends on) unit tests for courseware.

Notes for running by hand:

django-admin.py test --settings=lms.envs.test --pythonpath=. lms/djangoapps/instructor
"""

from courseware.access import _course_staff_group_name
from django.contrib.auth.models import \
    Group # Need access to internal func to put users in the right group
from django.core.urlresolvers import reverse
from django_comment_client.models import Role, FORUM_ROLE_ADMINISTRATOR, \
    FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA
from django_comment_client.utils import has_forum_access
from override_settings import override_settings
from xmodule.modulestore.django import modulestore
import courseware.tests.tests as ct
import xmodule.modulestore.django





@override_settings(MODULESTORE=ct.TEST_DATA_XML_MODULESTORE)
class TestInstructorDashboardGradeDownloadCSV(ct.PageLoader):
    '''
    Check for download of csv
    '''

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}
        courses = modulestore().get_courses()

        def find_course(name):
            """Assumes the course is present"""
            return [c for c in courses if c.location.course==name][0]

        self.full = find_course("full")
        self.toy = find_course("toy")

        # Create two accounts
        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)

        group_name = _course_staff_group_name(self.toy.location)
        g = Group.objects.create(name=group_name)
        g.user_set.add(ct.user(self.instructor))

        self.logout()
        self.login(self.instructor, self.password)
        self.enroll(self.toy)


    def test_download_grades_csv(self):
        print "running test_download_grades_csv"
        course = self.toy
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        msg = "url = %s\n" % url
        response = self.client.post(url, {'action': 'Download CSV of all student grades for this course',
                                          })
        msg += "instructor dashboard download csv grades: response = '%s'\n" % response

        self.assertEqual(response['Content-Type'],'text/csv',msg)

        cdisp = response['Content-Disposition'].replace('TT_2012','2012')  # jenkins course_id is TT_2012_Fall instead of 2012_Fall?
        msg += "cdisp = '%s'\n" % cdisp
        self.assertEqual(cdisp,'attachment; filename=grades_edX/toy/2012_Fall.csv',msg)

        body = response.content.replace('\r','')
        msg += "body = '%s'\n" % body

        expected_body = '''"ID","Username","Full Name","edX email","External email","HW 01","HW 02","HW 03","HW 04","HW 05","HW 06","HW 07","HW 08","HW 09","HW 10","HW 11","HW 12","HW Avg","Lab 01","Lab 02","Lab 03","Lab 04","Lab 05","Lab 06","Lab 07","Lab 08","Lab 09","Lab 10","Lab 11","Lab 12","Lab Avg","Midterm","Final"
"2","u2","Fred Weasley","view2@test.com","","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0.0","0.0"
'''
        self.assertEqual(body, expected_body, msg)
        
FORUM_ROLES = [ FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA ]
FORUM_ADMIN_ACTION_SUFFIX = { FORUM_ROLE_ADMINISTRATOR : 'admin', FORUM_ROLE_MODERATOR : 'moderator', FORUM_ROLE_COMMUNITY_TA : 'community TA'}
FORUM_ADMIN_USER = { FORUM_ROLE_ADMINISTRATOR : 'forumadmin', FORUM_ROLE_MODERATOR : 'forummoderator', FORUM_ROLE_COMMUNITY_TA : 'forummoderator'}

def action_name(operation, rolename):
    if operation == 'List':
        return '%s course forum %ss' % (operation, FORUM_ADMIN_ACTION_SUFFIX[rolename])
    else:
        return '%s forum %s' % (operation, FORUM_ADMIN_ACTION_SUFFIX[rolename])

@override_settings(MODULESTORE=ct.TEST_DATA_XML_MODULESTORE)
class TestInstructorDashboardForumAdmin(ct.PageLoader):
    '''
    Check for change in forum admin role memberships
    '''
    
    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}
        courses = modulestore().get_courses()

        def find_course(name):
            """Assumes the course is present"""
            return [c for c in courses if c.location.course==name][0]

        self.full = find_course("full")
        self.toy = find_course("toy")

        # Create two accounts
        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)

        group_name = _course_staff_group_name(self.toy.location)
        g = Group.objects.create(name=group_name)
        g.user_set.add(ct.user(self.instructor))

        self.logout()
        self.login(self.instructor, self.password)
        self.enroll(self.toy)

    def initialize_roles(self, course_id):
        self.admin_role = Role.objects.get_or_create(name=FORUM_ROLE_ADMINISTRATOR, course_id=course_id)[0]
        self.moderator_role = Role.objects.get_or_create(name=FORUM_ROLE_MODERATOR, course_id=course_id)[0]
        self.community_ta_role = Role.objects.get_or_create(name=FORUM_ROLE_COMMUNITY_TA, course_id=course_id)[0]

    def test_add_forum_admin_users_for_unknown_user(self):
        print "running test_add_forum_admin_users_for_unknown_user"
        course = self.toy
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'unknown'
        for action in ['Add', 'Remove']:
            for rolename in FORUM_ROLES:
                response = self.client.post(url, {'action': action_name(action, rolename), FORUM_ADMIN_USER[rolename]: username})
                self.assertTrue(response.content.find('Error: unknown username "%s"' % username)>=0)

    def test_add_forum_admin_users_for_missing_roles(self):
        print "test_add_forum_admin_users_for_missing_roles"
        course = self.toy
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u1'
        for action in ['Add', 'Remove']:
            for rolename in FORUM_ROLES:
                response = self.client.post(url, {'action': action_name(action, rolename), FORUM_ADMIN_USER[rolename]: username})
                self.assertTrue(response.content.find('Error: unknown rolename "%s"' % rolename)>=0)

    def test_remove_forum_admin_users_for_missing_users(self):
        print "test_remove_forum_admin_users_for_missing_users"
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u1'
        action = 'Remove'
        for rolename in FORUM_ROLES:
            response = self.client.post(url, {'action': action_name(action, rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(response.content.find('Error: user "%s" does not have rolename "%s"' % (username, rolename))>=0)

    def test_add_and_remove_forum_admin_users(self):
        print "test_add_and_remove_forum_admin_users"
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u2'
        for rolename in FORUM_ROLES:
            response = self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(response.content.find('Added "%s" to "%s" forum role = "%s"' % (username, course.id, rolename))>=0)
            self.assertTrue(has_forum_access(username, course.id, rolename))
            response = self.client.post(url, {'action': action_name('Remove', rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(response.content.find('Removed "%s" from "%s" forum role = "%s"' % (username, course.id, rolename))>=0)
            self.assertFalse(has_forum_access(username, course.id, rolename))

    def test_add_and_readd_forum_admin_users(self):
        print "test_add_and_readd_forum_admin_users"
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u2'
        for rolename in FORUM_ROLES:
            # perform an add, and follow with a second identical add:
            self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
            response = self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(response.content.find('Error: user "%s" already has rolename "%s", cannot add' % (username, rolename))>=0)
            self.assertTrue(has_forum_access(username, course.id, rolename))

    def test_add_nonstaff_forum_admin_users(self):
        print "test_add_and_readd_forum_admin_users"
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u1'
        rolename = FORUM_ROLE_ADMINISTRATOR
        response = self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
        self.assertTrue(response.content.find('Error: user "%s" should first be added as staff' % username)>=0)

    def test_list_forum_admin_users(self):
        print "test_list_forum_admin_users"
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u2'
        added_roles = ['Student']  # u2 is already added as a student to the discussion forums
        self.assertTrue(has_forum_access(username, course.id, 'Student'))
        for rolename in FORUM_ROLES:
            response = self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(has_forum_access(username, course.id, rolename))
            response = self.client.post(url, {'action': action_name('List', rolename), FORUM_ADMIN_USER[rolename]: username})
            for header in ['Username', 'Full name', 'Roles']:
                self.assertTrue(response.content.find('<th>%s</th>' % header)>0)
            self.assertTrue(response.content.find('<td>%s</td>' % username)>=0)
            # concatenate all roles for user, in sorted order:
            added_roles.append(rolename)
            added_roles.sort()
            roles = ', '.join(added_roles)
            self.assertTrue(response.content.find('<td>%s</td>' % roles)>=0, 'not finding roles "%s"' % roles)
