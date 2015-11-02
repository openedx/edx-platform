"""
Unit tests for course import and export
"""
import copy
import json
import logging
import lxml
import os
import tarfile
import tempfile
from path import path  # pylint: disable=no-name-in-module
from uuid import uuid4

from django.test.utils import override_settings
from django.conf import settings
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.xml_exporter import export_library_to_xml
from xmodule.modulestore.xml_importer import import_library_from_xml
from xmodule.modulestore import LIBRARY_ROOT
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.factories import ItemFactory, LibraryFactory

from .utils import CourseTestCase
from openedx.core.lib.extract_tar import safetar_extractall
from openedx.core.lib.tempdir import mkdtemp_clean
from student import auth
from student.roles import CourseInstructorRole, CourseStaffRole

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_{}'.format(
    uuid4().hex
)
TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT

log = logging.getLogger(__name__)


def course_url(handler, course_key, **kwargs):
    """
    Reverse a handler that uses a course key.

    :param handler: a URL handler name
    :param course_key: a CourseKey
    :return: the reversed URL string of the handler with the given course key
    """
    kwargs_for_reverse = {'course_key_string': course_key.id}
    if kwargs:
        kwargs_for_reverse.update(kwargs)

    return reverse(
        handler,
        kwargs=kwargs_for_reverse
    )


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ImportTestCase(CourseTestCase):
    """
    Unit tests for importing a course or library
    """
    def setUp(self):
        super(ImportTestCase, self).setUp()
        self.url = course_url('course_import_export_handler', self.course)
        self.content_dir = path(mkdtemp_clean())

        # Create tar test files -----------------------------------------------
        # OK course:
        good_dir = tempfile.mkdtemp(dir=self.content_dir)
        # test course being deeper down than top of tar file
        embedded_dir = os.path.join(good_dir, "grandparent", "parent")
        os.makedirs(os.path.join(embedded_dir, "course"))
        with open(os.path.join(embedded_dir, "course.xml"), "w+") as f:
            f.write('<course url_name="2013_Spring" org="EDx" course="0.00x"/>')

        with open(os.path.join(embedded_dir, "course", "2013_Spring.xml"), "w+") as f:
            f.write('<course></course>')

        self.good_tar = os.path.join(self.content_dir, "good.tar.gz")
        with tarfile.open(self.good_tar, "w:gz") as gtar:
            gtar.add(good_dir)

        # Bad course (no 'course.xml' file):
        bad_dir = tempfile.mkdtemp(dir=self.content_dir)
        path.joinpath(bad_dir, "bad.xml").touch()
        self.bad_tar = os.path.join(self.content_dir, "bad.tar.gz")
        with tarfile.open(self.bad_tar, "w:gz") as btar:
            btar.add(bad_dir)

        self.unsafe_common_dir = path(tempfile.mkdtemp(dir=self.content_dir))

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
        # Check that `ImportStatus` returns the appropriate stage (i.e., the
        # stage at which import failed).
        resp_status = self.client.get(
            course_url(
                'course_import_status_handler',
                self.course,
                filename=os.path.split(self.bad_tar)[1]
            )
        )

        obj = json.loads(resp_status.content)
        self.assertIn("ImportStatus", obj)
        self.assertEquals(obj["ImportStatus"], -2)

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
        Check that course is imported successfully in existing course and users
        have their access roles
        """
        # Create a non_staff user and add it to course staff only
        __, nonstaff_user = self.create_non_staff_authed_user_client()
        auth.add_users(
            self.user,
            CourseStaffRole(self.course.id),
            nonstaff_user
        )

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
        self.assertNotEqual(
            display_name_before_import,
            display_name_after_import
        )

        # Now check that non_staff user has his same role
        self.assertFalse(
            CourseInstructorRole(self.course.id).has_user(nonstaff_user)
        )
        self.assertTrue(
            CourseStaffRole(self.course.id).has_user(nonstaff_user)
        )

        # Now course staff user can also successfully import course
        self.client.login(username=nonstaff_user.username, password='foo')
        with open(self.good_tar) as gtar:
            args = {"name": self.good_tar, "course-data": [gtar]}
            resp = self.client.post(self.url, args)
        self.assertEquals(resp.status_code, 200)

        # Now check that non_staff user has his same role
        self.assertFalse(
            CourseInstructorRole(self.course.id).has_user(nonstaff_user)
        )
        self.assertTrue(
            CourseStaffRole(self.course.id).has_user(nonstaff_user)
        )

    ## Unsafe tar methods #####################################################
    # Each of these methods creates a tarfile with a single type of unsafe
    # content.
    def _create_tar_with_fifo(self):
        """
        Tar file with FIFO
        """
        fifop = self.unsafe_common_dir / "fifo.file"
        fifo_tar = self.unsafe_common_dir / "fifo.tar.gz"
        os.mkfifo(fifop)
        with tarfile.open(fifo_tar, "w:gz") as tar:
            tar.add(fifop)

        return fifo_tar

    def _create_tar_with_symlink(self):
        """
        Tarfile with symlink to path outside directory.
        """
        outsidep = self.unsafe_common_dir / "unsafe_file.txt"
        symlinkp = self.unsafe_common_dir / "symlink.txt"
        symlink_tar = self.unsafe_common_dir / "symlink.tar.gz"
        outsidep.symlink(symlinkp)  # pylint: disable=no-value-for-parameter
        with tarfile.open(symlink_tar, "w:gz") as tar:
            tar.add(symlinkp)

        return symlink_tar

    def _create_tar_file_outside(self, parent=False):
        """
        Tarfile that extracts to outside directory.

        If parent is False:
            The path of the file will match the basename
        (`self.unsafe_common_dir`), but then "cd's out".
            E.g. "/usr/../etc" == "/etc", but the naive basename of the first
        (but not the second) is "/usr"

        Extracting this tarfile in directory <dir> will put its contents
        directly in <dir> (rather than <dir/tarname>).
        """
        outside_tar = self.unsafe_common_dir / "unsafe_file.tar.gz"
        tarfile_path = str(
            self.unsafe_common_dir / "../a_file" if parent
            else self.content_dir / "a_file"
        )

        with tarfile.open(outside_tar, "w:gz") as tar:
            tar.addfile(
                tarfile.TarInfo(tarfile_path)
            )

        return outside_tar

    def _create_edx_platform_tar(self):
        """
        Tarfile with file that extracts to edx-platform directory.
        Extracting this tarfile in directory <dir> will also put its contents
        directly in <dir> (rather than <dir/tarname>).
        """
        outside_tar = self.unsafe_common_dir / "unsafe_file.tar.gz"
        with tarfile.open(outside_tar, "w:gz") as tar:
            tar.addfile(tarfile.TarInfo(os.path.join(os.path.abspath("."), "a_file")))

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
            """ Attempt to tar an unacceptable file """
            with open(tarpath) as tar:
                args = {"name": tarpath, "course-data": [tar]}
                resp = self.client.post(self.url, args)
            self.assertEquals(resp.status_code, 400)
            self.assertIn("suspicious_operation_message", resp.content)

        try_tar(self._create_tar_with_fifo())
        try_tar(self._create_tar_with_symlink())
        try_tar(self._create_tar_file_outside())
        try_tar(self._create_tar_file_outside(True))
        try_tar(self._create_edx_platform_tar())

        # test trying to open a tar outside of the normal data directory
        with self.settings(DATA_DIR='/not/the/data/dir'):
            try_tar(self._create_edx_platform_tar())

        # Check that `ImportStatus` returns the appropriate stage (i.e.,
        # either 3, indicating all previous steps are completed, or 0,
        # indicating no upload in progress)
        resp_status = self.client.get(
            course_url(
                'course_import_status_handler',
                self.course,
                filename=os.path.split(self.good_tar)[1]
            )
        )
        import_status = json.loads(resp_status.content)["ImportStatus"]
        self.assertIn(import_status, (0, 3))

    @override_settings(MODULESTORE_BRANCH='published')
    def test_library_import(self):
        """
        Try importing a known good library archive, and verify that the
        contents of the library have completely replaced the old contents.
        """
        # Create some blocks to overwrite
        library = LibraryFactory.create(modulestore=self.store)
        lib_key = library.location.library_key
        test_block = ItemFactory.create(
            category="vertical",
            parent_location=library.location,
            user_id=self.user.id,
            publish_item=False,
        )
        test_block2 = ItemFactory.create(
            category="vertical",
            parent_location=library.location,
            user_id=self.user.id,
            publish_item=False
        )
        # Create a library and blocks that should remain unmolested.
        unchanged_lib = LibraryFactory.create()
        unchanged_key = unchanged_lib.location.library_key
        test_block3 = ItemFactory.create(
            category="vertical",
            parent_location=unchanged_lib.location,
            user_id=self.user.id,
            publish_item=False
        )
        test_block4 = ItemFactory.create(
            category="vertical",
            parent_location=unchanged_lib.location,
            user_id=self.user.id,
            publish_item=False
        )
        # Refresh library.
        library = self.store.get_library(lib_key)
        children = [self.store.get_item(child).url_name for child in library.children]
        self.assertEqual(len(children), 2)
        self.assertIn(test_block.url_name, children)
        self.assertIn(test_block2.url_name, children)

        unchanged_lib = self.store.get_library(unchanged_key)
        children = [self.store.get_item(child).url_name for child in unchanged_lib.children]
        self.assertEqual(len(children), 2)
        self.assertIn(test_block3.url_name, children)
        self.assertIn(test_block4.url_name, children)

        extract_dir = path(mkdtemp_clean(dir=settings.DATA_DIR))
        # the extract_dir needs to be passed as a relative dir to
        # import_library_from_xml
        extract_dir_relative = path.relpath(extract_dir, settings.DATA_DIR)

        with tarfile.open(path(TEST_DATA_DIR) / 'imports' / 'library.HhJfPD.tar.gz') as tar:
            safetar_extractall(tar, extract_dir)
        library_items = import_library_from_xml(
            self.store,
            self.user.id,
            settings.GITHUB_REPO_ROOT,
            [extract_dir_relative / 'library'],
            load_error_modules=False,
            static_content_store=contentstore(),
            target_id=lib_key
        )

        self.assertEqual(lib_key, library_items[0].location.library_key)
        library = self.store.get_library(lib_key)
        children = [self.store.get_item(child).url_name for child in library.children]
        self.assertEqual(len(children), 3)
        self.assertNotIn(test_block.url_name, children)
        self.assertNotIn(test_block2.url_name, children)

        unchanged_lib = self.store.get_library(unchanged_key)
        children = [self.store.get_item(child).url_name for child in unchanged_lib.children]
        self.assertEqual(len(children), 2)
        self.assertIn(test_block3.url_name, children)
        self.assertIn(test_block4.url_name, children)


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
        self.url = course_url('course_import_export_handler', self.course)

    def test_export_html_unsupported(self):
        """
        HTML is unsupported
        """
        resp = self.client.get(self.url, HTTP_ACCEPT='text/html')
        self.assertEquals(resp.status_code, 406)

    def test_export_json_supported(self):
        """
        JSON is supported.
        """
        resp = self.client.get(self.url, HTTP_ACCEPT='application/json')
        self.assertEquals(resp.status_code, 200)

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
        resp = self.client.get(self.url + '?accept=application/x-tgz')
        self._verify_export_succeeded(resp)

    def _verify_export_succeeded(self, resp):
        """ Export success helper method. """
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(
            resp.get('Content-Disposition').startswith('attachment')
        )

    @override_settings(MODULESTORE_BRANCH='draft-preferred')
    def test_export_failure_top_level(self):
        """
        Export failure.
        """
        fake_xblock = ItemFactory.create(
            parent_location=self.course.location,
            category='aawefawef'
        )
        self.store.publish(fake_xblock.location, self.user.id)
        self._verify_export_failure(u'{}'.format(self.course.location))

    def test_export_failure_subsection_level(self):
        """
        Slightly different export failure.
        """
        vertical = ItemFactory.create(
            parent_location=self.course.location,
            category='vertical',
            display_name='foo')
        ItemFactory.create(
            parent_location=vertical.location,
            category='aawefawef'
        )

        self._verify_export_failure(u'{}'.format(vertical.location))

    def _verify_export_failure(self, expected_text):
        """ Export failure helper method. """
        resp = self.client.get(self.url, HTTP_ACCEPT='application/x-tgz')
        self.assertEquals(resp.status_code, 200)
        self.assertNotIn('Content-Disposition', resp)
        self.assertContains(resp, 'Unable to create xml for module')
        self.assertContains(resp, expected_text)

    def test_library_export(self):
        """
        Verify that useable library data can be exported.
        """
        youtube_id = "qS4NO9MNC6w"
        library = LibraryFactory.create(modulestore=self.store)
        video_block = ItemFactory.create(
            category="video",
            parent_location=library.location,
            user_id=self.user.id,
            publish_item=False,
            youtube_id_1_0=youtube_id
        )
        name = library.url_name
        lib_key = library.location.library_key
        root_dir = path(mkdtemp_clean())
        export_library_to_xml(self.store, contentstore(), lib_key, root_dir, name)
        lib_xml = lxml.etree.XML(open(root_dir / name / LIBRARY_ROOT).read())  # pylint: disable=no-member
        self.assertEqual(lib_xml.get('org'), lib_key.org)
        self.assertEqual(lib_xml.get('library'), lib_key.library)
        block = lib_xml.find('video')
        self.assertIsNotNone(block)
        self.assertEqual(block.get('url_name'), video_block.url_name)
        video_xml = lxml.etree.XML(  # pylint: disable=no-member
            open(root_dir / name / 'video' / video_block.url_name + '.xml').read()
        )
        self.assertEqual(video_xml.tag, 'video')
        self.assertEqual(video_xml.get('youtube_id_1_0'), youtube_id)

    def test_export_success_with_custom_tag(self):
        """
        Verify that course export with customtag
        """
        xml_string = '<impl>slides</impl>'
        vertical = ItemFactory.create(
            parent_location=self.course.location, category='vertical', display_name='foo'
        )
        ItemFactory.create(
            parent_location=vertical.location,
            category='customtag',
            display_name='custom_tag_foo',
            data=xml_string
        )

        self.test_export_targz_urlparam()
