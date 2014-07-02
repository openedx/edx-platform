"""
Unit tests for course import and export
"""
import copy
import json
import logging
import os
import shutil
import tarfile
import tempfile
from path import path
from pymongo import MongoClient
from uuid import uuid4

from django.test.utils import override_settings
from django.conf import settings
from contentstore.utils import reverse_course_url

from xmodule.contentstore.django import _CONTENTSTORE
from xmodule.modulestore.tests.factories import ItemFactory

from contentstore.tests.utils import CourseTestCase
from student import auth
from student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore.django import modulestore

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex

log = logging.getLogger(__name__)


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ImportTestCase(CourseTestCase):
    """
    Unit tests for importing a course
    """
    def setUp(self):
        super(ImportTestCase, self).setUp()
        self.url = reverse_course_url('import_handler', self.course.id)
        self.content_dir = path(tempfile.mkdtemp())

        def touch(name):
            """ Equivalent to shell's 'touch'"""
            with file(name, 'a'):
                os.utime(name, None)

        # Create tar test files -----------------------------------------------
        # OK course:
        good_dir = tempfile.mkdtemp(dir=self.content_dir)
        os.makedirs(os.path.join(good_dir, "course"))
        with open(os.path.join(good_dir, "course.xml"), "w+") as f:
            f.write('<course url_name="2013_Spring" org="EDx" course="0.00x"/>')

        with open(os.path.join(good_dir, "course", "2013_Spring.xml"), "w+") as f:
            f.write('<course></course>')

        self.good_tar = os.path.join(self.content_dir, "good.tar.gz")
        with tarfile.open(self.good_tar, "w:gz") as gtar:
            gtar.add(good_dir)

        # Bad course (no 'course.xml' file):
        bad_dir = tempfile.mkdtemp(dir=self.content_dir)
        touch(os.path.join(bad_dir, "bad.xml"))
        self.bad_tar = os.path.join(self.content_dir, "bad.tar.gz")
        with tarfile.open(self.bad_tar, "w:gz") as btar:
            btar.add(bad_dir)

        self.unsafe_common_dir = path(tempfile.mkdtemp(dir=self.content_dir))

    def tearDown(self):
        shutil.rmtree(self.content_dir)
        modulestore().contentstore.drop_database()
        _CONTENTSTORE.clear()

    def test_no_coursexml(self):
        """
        Check that the response for a tar.gz import without a course.xml is
        correct.
        """
        with open(self.bad_tar) as btar:
            resp = self.client.post(
                self.url,
                {
                    "name": self.bad_tar,
                    "course-data": [btar]
                })
        self.assertEquals(resp.status_code, 415)
        # Check that `import_status` returns the appropriate stage (i.e., the
        # stage at which import failed).
        resp_status = self.client.get(
            reverse_course_url(
                'import_status_handler',
                self.course.id,
                kwargs={'filename': os.path.split(self.bad_tar)[1]}
            )
        )

        self.assertEquals(json.loads(resp_status.content)["ImportStatus"], 2)

    def test_with_coursexml(self):
        """
        Check that the response for a tar.gz import with a course.xml is
        correct.
        """
        with open(self.good_tar) as gtar:
            args = {"name": self.good_tar, "course-data": [gtar]}
            resp = self.client.post(self.url, args)

        self.assertEquals(resp.status_code, 200)

    def test_import_in_existing_course(self):
        """
        Check that course is imported successfully in existing course and users have their access roles
        """
        # Create a non_staff user and add it to course staff only
        __, nonstaff_user = self.create_non_staff_authed_user_client(authenticate=False)
        auth.add_users(self.user, CourseStaffRole(self.course.id), nonstaff_user)

        course = self.store.get_course(self.course.id)
        self.assertIsNotNone(course)
        display_name_before_import = course.display_name

        # Check that global staff user can import course
        with open(self.good_tar) as gtar:
            args = {"name": self.good_tar, "course-data": [gtar]}
            resp = self.client.post(self.url, args)
        self.assertEquals(resp.status_code, 200)

        course = self.store.get_course(self.course.id)
        self.assertIsNotNone(course)
        display_name_after_import = course.display_name

        # Check that course display name have changed after import
        self.assertNotEqual(display_name_before_import, display_name_after_import)

        # Now check that non_staff user has his same role
        self.assertFalse(CourseInstructorRole(self.course.id).has_user(nonstaff_user))
        self.assertTrue(CourseStaffRole(self.course.id).has_user(nonstaff_user))

        # Now course staff user can also successfully import course
        self.client.login(username=nonstaff_user.username, password='foo')
        with open(self.good_tar) as gtar:
            args = {"name": self.good_tar, "course-data": [gtar]}
            resp = self.client.post(self.url, args)
        self.assertEquals(resp.status_code, 200)

        # Now check that non_staff user has his same role
        self.assertFalse(CourseInstructorRole(self.course.id).has_user(nonstaff_user))
        self.assertTrue(CourseStaffRole(self.course.id).has_user(nonstaff_user))

    ## Unsafe tar methods #####################################################
    # Each of these methods creates a tarfile with a single type of unsafe
    # content.
    def _fifo_tar(self):
        """
        Tar file with FIFO
        """
        fifop = self.unsafe_common_dir / "fifo.file"
        fifo_tar = self.unsafe_common_dir / "fifo.tar.gz"
        os.mkfifo(fifop)
        with tarfile.open(fifo_tar, "w:gz") as tar:
            tar.add(fifop)

        return fifo_tar

    def _symlink_tar(self):
        """
        Tarfile with symlink to path outside directory.
        """
        outsidep = self.unsafe_common_dir / "unsafe_file.txt"
        symlinkp = self.unsafe_common_dir / "symlink.txt"
        symlink_tar = self.unsafe_common_dir / "symlink.tar.gz"
        outsidep.symlink(symlinkp)
        with tarfile.open(symlink_tar, "w:gz") as tar:
            tar.add(symlinkp)

        return symlink_tar

    def _outside_tar(self):
        """
        Tarfile with file that extracts to outside directory.

        Extracting this tarfile in directory <dir> will put its contents
        directly in <dir> (rather than <dir/tarname>).
        """
        outside_tar = self.unsafe_common_dir / "unsafe_file.tar.gz"
        with tarfile.open(outside_tar, "w:gz") as tar:
            tar.addfile(tarfile.TarInfo(str(self.content_dir / "a_file")))

        return outside_tar

    def _outside_tar2(self):
        """
        Tarfile with file that extracts to outside directory.

        The path here matches the basename (`self.unsafe_common_dir`), but
        then "cd's out". E.g. "/usr/../etc" == "/etc", but the naive basename
        of the first (but not the second) is "/usr"

        Extracting this tarfile in directory <dir> will also put its contents
        directly in <dir> (rather than <dir/tarname>).
        """
        outside_tar = self.unsafe_common_dir / "unsafe_file.tar.gz"
        with tarfile.open(outside_tar, "w:gz") as tar:
            tar.addfile(tarfile.TarInfo(str(self.unsafe_common_dir / "../a_file")))

        return outside_tar

    def test_unsafe_tar(self):
        """
        Check that safety measure work.

        This includes:
            'tarbombs' which include files or symlinks with paths
        outside or directly in the working directory,
            'special files' (character device, block device or FIFOs),

        all raise exceptions/400s.
        """

        def try_tar(tarpath):
            with open(tarpath) as tar:
                args = {"name": tarpath, "course-data": [tar]}
                resp = self.client.post(self.url, args)
            self.assertEquals(resp.status_code, 400)
            self.assertTrue("SuspiciousFileOperation" in resp.content)

        try_tar(self._fifo_tar())
        try_tar(self._symlink_tar())
        try_tar(self._outside_tar())
        try_tar(self._outside_tar2())
        # Check that `import_status` returns the appropriate stage (i.e.,
        # either 3, indicating all previous steps are completed, or 0,
        # indicating no upload in progress)
        resp_status = self.client.get(
            reverse_course_url(
                'import_status_handler',
                self.course.id,
                kwargs={'filename': os.path.split(self.good_tar)[1]}
            )
        )
        import_status = json.loads(resp_status.content)["ImportStatus"]
        self.assertIn(import_status, (0, 3))


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ExportTestCase(CourseTestCase):
    """
    Tests for export_handler.
    """
    def setUp(self):
        """
        Sets up the test course.
        """
        super(ExportTestCase, self).setUp()
        self.url = reverse_course_url('export_handler', self.course.id)

    def test_export_html(self):
        """
        Get the HTML for the page.
        """
        resp = self.client.get_html(self.url)
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, "Export My Course Content")

    def test_export_json_unsupported(self):
        """
        JSON is unsupported.
        """
        resp = self.client.get(self.url, HTTP_ACCEPT='application/json')
        self.assertEquals(resp.status_code, 406)

    def test_export_targz(self):
        """
        Get tar.gz file, using HTTP_ACCEPT.
        """
        resp = self.client.get(self.url, HTTP_ACCEPT='application/x-tgz')
        self._verify_export_succeeded(resp)

    def test_export_targz_urlparam(self):
        """
        Get tar.gz file, using URL parameter.
        """
        resp = self.client.get(self.url + '?_accept=application/x-tgz')
        self._verify_export_succeeded(resp)

    def _verify_export_succeeded(self, resp):
        """ Export success helper method. """
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(resp.get('Content-Disposition').startswith('attachment'))

    def test_export_failure_top_level(self):
        """
        Export failure.
        """
        fake_xblock = ItemFactory.create(parent_location=self.course.location, category='aawefawef')
        self.store.publish(fake_xblock.location, self.user.id)
        self._verify_export_failure(u'/unit/i4x://MITx/999/course/Robot_Super_Course')

    def test_export_failure_subsection_level(self):
        """
        Slightly different export failure.
        """
        vertical = ItemFactory.create(parent_location=self.course.location, category='vertical', display_name='foo')
        ItemFactory.create(
            parent_location=vertical.location,
            category='aawefawef'
        )

        self._verify_export_failure(u'/unit/i4x://MITx/999/vertical/foo')

    def _verify_export_failure(self, expectedText):
        """ Export failure helper method. """
        resp = self.client.get(self.url, HTTP_ACCEPT='application/x-tgz')
        self.assertEquals(resp.status_code, 200)
        self.assertIsNone(resp.get('Content-Disposition'))
        self.assertContains(resp, 'Unable to create xml for module')
        self.assertContains(resp, expectedText)
