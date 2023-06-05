"""
Unit tests for course import and export
"""

import copy
import json
import logging
import os
import re
import shutil
import tarfile
import tempfile
from uuid import uuid4

import ddt
import lxml
import six
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.test.utils import override_settings
from milestones.tests.utils import MilestonesTestCaseMixin
from mock import Mock, patch
from opaque_keys.edx.locator import LibraryLocator
from path import Path as path
from six.moves import zip
from storages.backends.s3boto import S3BotoStorage
from user_tasks.models import UserTaskStatus

from cms.djangoapps.contentstore.tests.test_libraries import LibraryTestCase
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.utils import reverse_course_url
from cms.djangoapps.models.settings.course_metadata import CourseMetadata
from openedx.core.lib.extract_tar import safetar_extractall
from common.djangoapps.student import auth
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from common.djangoapps.util import milestones_helpers
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import LIBRARY_ROOT, ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, LibraryFactory
from xmodule.modulestore.tests.utils import SPLIT_MODULESTORE_SETUP, TEST_DATA_DIR, MongoContentstoreBuilder
from xmodule.modulestore.xml_exporter import export_course_to_xml, export_library_to_xml
from xmodule.modulestore.xml_importer import import_course_from_xml, import_library_from_xml

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex
TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT

log = logging.getLogger(__name__)


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ImportEntranceExamTestCase(CourseTestCase, MilestonesTestCaseMixin):
    """
    Unit tests for importing a course with entrance exam
    """

    def setUp(self):
        super(ImportEntranceExamTestCase, self).setUp()
        self.url = reverse_course_url('import_handler', self.course.id)
        self.content_dir = path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.content_dir)

        # Create tar test file -----------------------------------------------
        # OK course with entrance exam section:
        entrance_exam_dir = tempfile.mkdtemp(dir=self.content_dir)
        # test course being deeper down than top of tar file
        embedded_exam_dir = os.path.join(entrance_exam_dir, "grandparent", "parent")
        os.makedirs(os.path.join(embedded_exam_dir, "course"))
        os.makedirs(os.path.join(embedded_exam_dir, "chapter"))
        with open(os.path.join(embedded_exam_dir, "course.xml"), "w+") as f:
            f.write('<course url_name="2013_Spring" org="EDx" course="0.00x"/>')

        with open(os.path.join(embedded_exam_dir, "course", "2013_Spring.xml"), "w+") as f:
            f.write(
                '<course '
                'entrance_exam_enabled="true" entrance_exam_id="xyz" entrance_exam_minimum_score_pct="0.7">'
                '<chapter url_name="2015_chapter_entrance_exam"/></course>'
            )

        with open(os.path.join(embedded_exam_dir, "chapter", "2015_chapter_entrance_exam.xml"), "w+") as f:
            f.write('<chapter display_name="Entrance Exam" in_entrance_exam="true" is_entrance_exam="true"></chapter>')

        self.entrance_exam_tar = os.path.join(self.content_dir, "entrance_exam.tar.gz")
        with tarfile.open(self.entrance_exam_tar, "w:gz") as gtar:
            gtar.add(entrance_exam_dir)

    def test_import_existing_entrance_exam_course(self):
        """
        Check that course is imported successfully as an entrance exam.
        """
        course = self.store.get_course(self.course.id)
        self.assertIsNotNone(course)
        self.assertEqual(course.entrance_exam_enabled, False)

        with open(self.entrance_exam_tar, 'rb') as gtar:  # pylint: disable=open-builtin
            args = {"name": self.entrance_exam_tar, "course-data": [gtar]}
            resp = self.client.post(self.url, args)
        self.assertEqual(resp.status_code, 200)
        course = self.store.get_course(self.course.id)
        self.assertIsNotNone(course)
        self.assertEqual(course.entrance_exam_enabled, True)
        self.assertEqual(course.entrance_exam_minimum_score_pct, 0.7)

    def test_import_delete_pre_exiting_entrance_exam(self):
        """
        Check that pre existed entrance exam content should be overwrite with the imported course.
        """
        exam_url = '/course/{}/entrance_exam/'.format(six.text_type(self.course.id))
        resp = self.client.post(exam_url, {'entrance_exam_minimum_score_pct': 0.5}, http_accept='application/json')
        self.assertEqual(resp.status_code, 201)

        # Reload the test course now that the exam module has been added
        self.course = modulestore().get_course(self.course.id)
        metadata = CourseMetadata.fetch_all(self.course)
        self.assertTrue(metadata['entrance_exam_enabled'])
        self.assertIsNotNone(metadata['entrance_exam_minimum_score_pct'])
        self.assertEqual(metadata['entrance_exam_minimum_score_pct']['value'], 0.5)
        self.assertTrue(len(milestones_helpers.get_course_milestones(six.text_type(self.course.id))))
        content_milestones = milestones_helpers.get_course_content_milestones(
            six.text_type(self.course.id),
            metadata['entrance_exam_id']['value'],
            milestones_helpers.get_milestone_relationship_types()['FULFILLS']
        )
        self.assertTrue(len(content_milestones))

        # Now import entrance exam course
        with open(self.entrance_exam_tar, 'rb') as gtar:  # pylint: disable=open-builtin
            args = {"name": self.entrance_exam_tar, "course-data": [gtar]}
            resp = self.client.post(self.url, args)
        self.assertEqual(resp.status_code, 200)
        course = self.store.get_course(self.course.id)
        self.assertIsNotNone(course)
        self.assertEqual(course.entrance_exam_enabled, True)
        self.assertEqual(course.entrance_exam_minimum_score_pct, 0.7)


@ddt.ddt
@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ImportTestCase(CourseTestCase):
    """
    Unit tests for importing a course or Library
    """
    CREATE_USER = True

    def setUp(self):
        super(ImportTestCase, self).setUp()
        self.url = reverse_course_url('import_handler', self.course.id)
        self.content_dir = path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.content_dir)

        def touch(name):
            """ Equivalent to shell's 'touch'"""
            with open(name, 'a'):  # pylint: disable=W6005
                os.utime(name, None)

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
        touch(os.path.join(bad_dir, "bad.xml"))
        self.bad_tar = os.path.join(self.content_dir, "bad.tar.gz")
        with tarfile.open(self.bad_tar, "w:gz") as btar:
            btar.add(bad_dir)

        self.unsafe_common_dir = path(tempfile.mkdtemp(dir=self.content_dir))

    def test_no_coursexml(self):
        """
        Check that the response for a tar.gz import without a course.xml is
        correct.
        """
        with open(self.bad_tar, 'rb') as btar:  # pylint: disable=open-builtin
            resp = self.client.post(
                self.url,
                {
                    "name": self.bad_tar,
                    "course-data": [btar]
                })
        self.assertEqual(resp.status_code, 200)
        # Check that `import_status` returns the appropriate stage (i.e., the
        # stage at which import failed).
        resp_status = self.client.get(
            reverse_course_url(
                'import_status_handler',
                self.course.id,
                kwargs={'filename': os.path.split(self.bad_tar)[1]}
            )
        )

        self.assertEqual(json.loads(resp_status.content.decode('utf-8'))["ImportStatus"], -2)

    def test_with_coursexml(self):
        """
        Check that the response for a tar.gz import with a course.xml is
        correct.
        """
        with open(self.good_tar, 'rb') as gtar:  # pylint: disable=open-builtin
            args = {"name": self.good_tar, "course-data": [gtar]}
            resp = self.client.post(self.url, args)

        self.assertEqual(resp.status_code, 200)

    def test_import_in_existing_course(self):
        """
        Check that course is imported successfully in existing course and users have their access roles
        """
        # Create a non_staff user and add it to course staff only
        __, nonstaff_user = self.create_non_staff_authed_user_client()
        auth.add_users(self.user, CourseStaffRole(self.course.id), nonstaff_user)

        course = self.store.get_course(self.course.id)
        self.assertIsNotNone(course)
        display_name_before_import = course.display_name

        # Check that global staff user can import course
        with open(self.good_tar, 'rb') as gtar:  # pylint: disable=open-builtin
            args = {"name": self.good_tar, "course-data": [gtar]}
            resp = self.client.post(self.url, args)
        self.assertEqual(resp.status_code, 200)

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
        with open(self.good_tar, 'rb') as gtar:  # pylint: disable=open-builtin
            args = {"name": self.good_tar, "course-data": [gtar]}
            resp = self.client.post(self.url, args)
        self.assertEqual(resp.status_code, 200)

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

    def _edx_platform_tar(self):
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
            with open(tarpath, 'rb') as tar:  # pylint: disable=open-builtin
                args = {"name": tarpath, "course-data": [tar]}
                resp = self.client.post(self.url, args)
            self.assertEqual(resp.status_code, 200)
            resp = self.client.get(
                reverse_course_url(
                    'import_status_handler',
                    self.course.id,
                    kwargs={'filename': os.path.split(tarpath)[1]}
                )
            )
            status = json.loads(resp.content.decode('utf-8'))["ImportStatus"]
            self.assertEqual(status, -1)

        try_tar(self._fifo_tar())
        try_tar(self._symlink_tar())
        try_tar(self._outside_tar())
        try_tar(self._outside_tar2())
        try_tar(self._edx_platform_tar())

        # test trying to open a tar outside of the normal data directory
        with self.settings(DATA_DIR='/not/the/data/dir'):
            try_tar(self._edx_platform_tar())

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
        import_status = json.loads(resp_status.content.decode('utf-8'))["ImportStatus"]
        self.assertIn(import_status, (0, 3))

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

        extract_dir = path(tempfile.mkdtemp(dir=settings.DATA_DIR))
        # the extract_dir needs to be passed as a relative dir to
        # import_library_from_xml
        extract_dir_relative = path.relpath(extract_dir, settings.DATA_DIR)

        try:
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
        finally:
            shutil.rmtree(extract_dir)

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

    @ddt.data(
        ModuleStoreEnum.Branch.draft_preferred,
        ModuleStoreEnum.Branch.published_only,
    )
    def test_library_import_branch_settings(self, branch_setting):
        """
        Try importing a known good library archive under either branch setting.
        The branch setting should have no effect on library import.
        """
        with self.store.branch_setting(branch_setting):
            library = LibraryFactory.create(modulestore=self.store)
            lib_key = library.location.library_key
            extract_dir = path(tempfile.mkdtemp(dir=settings.DATA_DIR))
            # the extract_dir needs to be passed as a relative dir to
            # import_library_from_xml
            extract_dir_relative = path.relpath(extract_dir, settings.DATA_DIR)

            try:
                with tarfile.open(path(TEST_DATA_DIR) / 'imports' / 'library.HhJfPD.tar.gz') as tar:
                    safetar_extractall(tar, extract_dir)
                import_library_from_xml(
                    self.store,
                    self.user.id,
                    settings.GITHUB_REPO_ROOT,
                    [extract_dir_relative / 'library'],
                    load_error_modules=False,
                    static_content_store=contentstore(),
                    target_id=lib_key
                )
            finally:
                shutil.rmtree(extract_dir)

    @ddt.data(
        ModuleStoreEnum.Branch.draft_preferred,
        ModuleStoreEnum.Branch.published_only,
    )
    def test_library_import_branch_settings_again(self, branch_setting):
        # Construct the contentstore for storing the import
        with MongoContentstoreBuilder().build() as source_content:
            # Construct the modulestore for storing the import (using the previously created contentstore)
            with SPLIT_MODULESTORE_SETUP.build(contentstore=source_content) as source_store:
                # Use the test branch setting.
                with source_store.branch_setting(branch_setting):
                    source_library_key = LibraryLocator(org='TestOrg', library='TestProbs')

                    extract_dir = path(tempfile.mkdtemp(dir=settings.DATA_DIR))
                    # the extract_dir needs to be passed as a relative dir to
                    # import_library_from_xml
                    extract_dir_relative = path.relpath(extract_dir, settings.DATA_DIR)

                    try:
                        with tarfile.open(path(TEST_DATA_DIR) / 'imports' / 'library.HhJfPD.tar.gz') as tar:
                            safetar_extractall(tar, extract_dir)
                        import_library_from_xml(
                            source_store,
                            self.user.id,
                            settings.GITHUB_REPO_ROOT,
                            [extract_dir_relative / 'library'],
                            static_content_store=source_content,
                            target_id=source_library_key,
                            load_error_modules=False,
                            raise_on_failure=True,
                            create_if_not_present=True,
                        )
                    finally:
                        shutil.rmtree(extract_dir)


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
@ddt.ddt
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
        self.status_url = reverse_course_url('export_status_handler', self.course.id)

    def test_export_html(self):
        """
        Get the HTML for the page.
        """
        resp = self.client.get_html(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Export My Course Content")

    def test_export_json_unsupported(self):
        """
        JSON is unsupported.
        """
        resp = self.client.get(self.url, HTTP_ACCEPT='application/json')
        self.assertEqual(resp.status_code, 406)

    def test_export_async(self):
        """
        Get tar.gz file, using asynchronous background task

        Return a TarFile of the successful export.
        """
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(self.status_url)
        result = json.loads(resp.content.decode('utf-8'))
        status = result['ExportStatus']
        self.assertEqual(status, 3)
        self.assertIn('ExportOutput', result)
        output_url = result['ExportOutput']
        resp = self.client.get(output_url)
        self._verify_export_succeeded(resp)
        resp_content = b''
        for item in resp.streaming_content:
            resp_content += item

        buff = six.BytesIO(resp_content)
        return tarfile.open(fileobj=buff)

    def _verify_export_succeeded(self, resp):
        """ Export success helper method. """
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get('Content-Disposition').startswith('attachment'))

    def test_unknown_xblock_top_level(self):
        """
        Export unknown XBlock type (i.e. we uninstalled the XBlock), top level.
        """
        fake_xblock = ItemFactory.create(
            parent_location=self.course.location,
            category='not_a_real_block_type'
        )
        self.store.publish(fake_xblock.location, self.user.id)

        # Now check the resulting export
        tar_ball = self.test_export_async()
        course_file_path = next(
            path for path in tar_ball.getnames()
            if re.match(r'\w+/course/\w+.xml', path)
        )
        course_file = tar_ball.extractfile(course_file_path)
        course_xml = lxml.etree.parse(course_file)
        course_elem = course_xml.getroot()

        # The course run file still has a child pointer to the unknown type and
        # creates the <not_a_real_block_type url="..."> pointer tag...
        self.assertEqual(course_elem.tag, 'course')
        unknown_elem = course_elem[0]
        self.assertEqual(unknown_elem.tag, 'not_a_real_block_type')
        # Non empty url_name attribute (the generated ID)
        self.assertTrue(unknown_elem.attrib['url_name'])

        # But there should be no file exported for our fake block type. Without
        # the XBlock installed, we don't know how to serialize it properly.
        assert not any(
            '/not_a_real_block_type/' in path
            for path in tar_ball.getnames()
        )

    def test_unknown_xblock_subsection_level(self):
        """
        Export unknown XBlock type deeper in the course.
        """
        vertical = ItemFactory.create(
            parent_location=self.course.location,
            category='vertical',
            display_name='sample_vertical',
        )
        fake_xblock = ItemFactory.create(
            parent_location=vertical.location,
            category='not_a_real_block_type',
        )
        self.store.publish(fake_xblock.location, self.user.id)

        # Now check the resulting export
        tar_ball = self.test_export_async()
        course_file_path = next(
            path for path in tar_ball.getnames()
            if re.match(r'\w+/course/\w+.xml', path)
        )
        course_file = tar_ball.extractfile(course_file_path)
        course_xml = lxml.etree.parse(course_file)
        course_elem = course_xml.getroot()

        # The course run file should have a vertical that points to the
        # non-existant block.
        self.assertEqual(course_elem.tag, 'course')
        self.assertEqual(course_elem[0].tag, 'vertical')  # This is just a reference

        vert_file_path = next(
            path for path in tar_ball.getnames()
            if re.match(r'\w+/vertical/\w+.xml', path)
        )
        vert_file = tar_ball.extractfile(vert_file_path)
        vert_xml = lxml.etree.parse(vert_file)
        vert_elem = vert_xml.getroot()
        self.assertEqual(vert_elem.tag, 'vertical')
        self.assertEqual(len(vert_elem), 1)
        unknown_elem = vert_elem[0]
        self.assertEqual(unknown_elem.tag, 'not_a_real_block_type')
        # Non empty url_name attribute (the generated ID)
        self.assertTrue(unknown_elem.attrib['url_name'])

        # There should be no file exported for our fake block type
        assert not any(
            '/not_a_real_block_type/' in path
            for path in tar_ball.getnames()
        )

    def _verify_export_failure(self, expected_text):
        """ Export failure helper method. """
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(self.status_url)
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content.decode('utf-8'))
        self.assertNotIn('ExportOutput', result)
        self.assertIn('ExportError', result)
        error = result['ExportError']
        self.assertIn('Unable to create xml for module', error['raw_error_msg'])
        self.assertIn(expected_text, error['edit_unit_url'])

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
        root_dir = path(tempfile.mkdtemp())
        try:
            export_library_to_xml(self.store, contentstore(), lib_key, root_dir, name)
            lib_xml = lxml.etree.XML(open(root_dir / name / LIBRARY_ROOT).read())
            self.assertEqual(lib_xml.get('org'), lib_key.org)
            self.assertEqual(lib_xml.get('library'), lib_key.library)
            block = lib_xml.find('video')
            self.assertIsNotNone(block)
            self.assertEqual(block.get('url_name'), video_block.url_name)
            video_xml = lxml.etree.XML(open(root_dir / name / 'video' / video_block.url_name + '.xml').read())
            self.assertEqual(video_xml.tag, 'video')
            self.assertEqual(video_xml.get('youtube_id_1_0'), youtube_id)
        finally:
            shutil.rmtree(root_dir / name)

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

        self.test_export_async()

    @ddt.data(
        '/export/non.1/existence_1/Run_1',  # For mongo
        '/export/course-v1:non1+existence1+Run1',  # For split
    )
    def test_export_course_does_not_exist(self, url):
        """
        Export failure if course does not exist
        """
        resp = self.client.get_html(url)
        self.assertEqual(resp.status_code, 404)

    def test_non_course_author(self):
        """
        Verify that users who aren't authors of the course are unable to export it
        """
        client, _ = self.create_non_staff_authed_user_client()
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_status_non_course_author(self):
        """
        Verify that users who aren't authors of the course are unable to see the status of export tasks
        """
        client, _ = self.create_non_staff_authed_user_client()
        resp = client.get(self.status_url)
        self.assertEqual(resp.status_code, 403)

    def test_status_missing_record(self):
        """
        Attempting to get the status of an export task which isn't currently
        represented in the database should yield a useful result
        """
        resp = self.client.get(self.status_url)
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(result['ExportStatus'], 0)

    def test_output_non_course_author(self):
        """
        Verify that users who aren't authors of the course are unable to see the output of export tasks
        """
        client, _ = self.create_non_staff_authed_user_client()
        resp = client.get(reverse_course_url('export_output_handler', self.course.id))
        self.assertEqual(resp.status_code, 403)

    def _mock_artifact(self, spec=None, file_url=None):
        """
        Creates a Mock of the UserTaskArtifact model for testing exports handler
        code without touching the database.
        """
        mock_artifact = Mock()
        mock_artifact.file.name = 'testfile.tar.gz'
        mock_artifact.file.storage = Mock(spec=spec)
        mock_artifact.file.storage.url.return_value = file_url
        return mock_artifact

    @patch('cms.djangoapps.contentstore.views.import_export._latest_task_status')
    @patch('user_tasks.models.UserTaskArtifact.objects.get')
    def test_export_status_handler_other(
        self,
        mock_get_user_task_artifact,
        mock_latest_task_status,
    ):
        """
        Verify that the export status handler generates the correct export path
        for storage providers other than ``FileSystemStorage`` and
        ``S3BotoStorage``
        """
        mock_latest_task_status.return_value = Mock(state=UserTaskStatus.SUCCEEDED)
        mock_get_user_task_artifact.return_value = self._mock_artifact(
            file_url='/path/to/testfile.tar.gz',
        )
        resp = self.client.get(self.status_url)
        result = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(result['ExportOutput'], '/path/to/testfile.tar.gz')

    @patch('cms.djangoapps.contentstore.views.import_export._latest_task_status')
    @patch('user_tasks.models.UserTaskArtifact.objects.get')
    def test_export_status_handler_s3(
        self,
        mock_get_user_task_artifact,
        mock_latest_task_status,
    ):
        """
        Verify that the export status handler generates the correct export path
        for the ``S3BotoStorage`` storage provider
        """
        mock_latest_task_status.return_value = Mock(state=UserTaskStatus.SUCCEEDED)
        mock_get_user_task_artifact.return_value = self._mock_artifact(
            spec=S3BotoStorage,
            file_url='/s3/file/path/testfile.tar.gz',
        )
        resp = self.client.get(self.status_url)
        result = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(result['ExportOutput'], '/s3/file/path/testfile.tar.gz')

    @patch('cms.djangoapps.contentstore.views.import_export._latest_task_status')
    @patch('user_tasks.models.UserTaskArtifact.objects.get')
    def test_export_status_handler_filesystem(
        self,
        mock_get_user_task_artifact,
        mock_latest_task_status,
    ):
        """
        Verify that the export status handler generates the correct export path
        for the ``FileSystemStorage`` storage provider
        """
        mock_latest_task_status.return_value = Mock(state=UserTaskStatus.SUCCEEDED)
        mock_get_user_task_artifact.return_value = self._mock_artifact(spec=FileSystemStorage)
        resp = self.client.get(self.status_url)
        result = json.loads(resp.content.decode('utf-8'))
        file_export_output_url = reverse_course_url('export_output_handler', self.course.id)
        self.assertEqual(result['ExportOutput'], file_export_output_url)


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class TestLibraryImportExport(CourseTestCase):
    """
    Tests for importing content libraries from XML and exporting them to XML.
    """

    def setUp(self):
        super(TestLibraryImportExport, self).setUp()
        self.export_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.export_dir, ignore_errors=True)

    def test_content_library_export_import(self):
        library1 = LibraryFactory.create(modulestore=self.store)
        source_library1_key = library1.location.library_key
        library2 = LibraryFactory.create(modulestore=self.store)
        source_library2_key = library2.location.library_key

        import_library_from_xml(
            self.store,
            'test_user',
            TEST_DATA_DIR,
            ['library_empty_problem'],
            static_content_store=contentstore(),
            target_id=source_library1_key,
            load_error_modules=False,
            raise_on_failure=True,
            create_if_not_present=True,
        )

        export_library_to_xml(
            self.store,
            contentstore(),
            source_library1_key,
            self.export_dir,
            'exported_source_library',
        )

        source_library = self.store.get_library(source_library1_key)
        self.assertEqual(source_library.url_name, 'library')

        # Import the exported library into a different content library.
        import_library_from_xml(
            self.store,
            'test_user',
            self.export_dir,
            ['exported_source_library'],
            static_content_store=contentstore(),
            target_id=source_library2_key,
            load_error_modules=False,
            raise_on_failure=True,
            create_if_not_present=True,
        )

        # Compare the two content libraries for equality.
        self.assertCoursesEqual(source_library1_key, source_library2_key)


@ddt.ddt
@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class TestCourseExportImport(LibraryTestCase):
    """
    Tests for importing after exporting the course containing content libraries from XML.
    """

    def setUp(self):
        super(TestCourseExportImport, self).setUp()
        self.export_dir = tempfile.mkdtemp()

        # Create a problem in library
        ItemFactory.create(
            category="problem",
            parent_location=self.library.location,
            user_id=self.user.id,
            publish_item=False,
            display_name='Test Problem',
            data="<problem><multiplechoiceresponse></multiplechoiceresponse></problem>",
        )

        # Create a source course.
        self.source_course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        self.addCleanup(shutil.rmtree, self.export_dir, ignore_errors=True)

    def _setup_source_course_with_library_content(self, publish=False):
        """
        Sets up course with library content.
        """
        chapter = ItemFactory.create(
            parent_location=self.source_course.location,
            category='chapter',
            display_name='Test Section'
        )
        sequential = ItemFactory.create(
            parent_location=chapter.location,
            category='sequential',
            display_name='Test Sequential'
        )
        vertical = ItemFactory.create(
            category='vertical',
            parent_location=sequential.location,
            display_name='Test Unit'
        )
        lc_block = self._add_library_content_block(vertical, self.lib_key, publish_item=publish)
        self._refresh_children(lc_block)

    def get_lib_content_block_children(self, block_location):
        """
        Search for library content block to return its immediate children
        """
        if block_location.block_type == 'library_content':
            return self.store.get_item(block_location).children

        return self.get_lib_content_block_children(self.store.get_item(block_location).children[0])

    def assert_problem_display_names(self, source_course_location, dest_course_location, is_published):
        """
        Asserts that problems' display names in both source and destination courses are same.
        """
        source_course_lib_children = self.get_lib_content_block_children(source_course_location)
        dest_course_lib_children = self.get_lib_content_block_children(dest_course_location)

        self.assertEqual(len(source_course_lib_children), len(dest_course_lib_children))

        for source_child_location, dest_child_location in zip(source_course_lib_children, dest_course_lib_children):
            # Assert problem names on draft branch.
            with self.store.branch_setting(branch_setting=ModuleStoreEnum.Branch.draft_preferred):
                self.assert_names(source_child_location, dest_child_location)

            if is_published:
                # Assert problem names on publish branch.
                with self.store.branch_setting(branch_setting=ModuleStoreEnum.Branch.published_only):
                    self.assert_names(source_child_location, dest_child_location)

    def assert_names(self, source_child_location, dest_child_location):
        """
        Check if blocks have same display_name.
        """
        source_child = self.store.get_item(source_child_location)
        dest_child = self.store.get_item(dest_child_location)
        self.assertEqual(source_child.display_name, dest_child.display_name)

    @ddt.data(True, False)
    def test_library_content_on_course_export_import(self, publish_item):
        """
        Verify that library contents in destination and source courses are same after importing
        the source course into destination course.
        """
        self._setup_source_course_with_library_content(publish=publish_item)

        # Create a course to import source course.
        dest_course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)

        # Export the source course.
        export_course_to_xml(
            self.store,
            contentstore(),
            self.source_course.location.course_key,
            self.export_dir,
            'exported_source_course',
        )

        # Now, import it back to dest_course.
        import_course_from_xml(
            self.store,
            self.user.id,
            self.export_dir,
            ['exported_source_course'],
            static_content_store=contentstore(),
            target_id=dest_course.location.course_key,
            load_error_modules=False,
            raise_on_failure=True,
            create_if_not_present=True,
        )

        self.assert_problem_display_names(
            self.source_course.location,
            dest_course.location,
            publish_item
        )


@ddt.ddt
@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class TestCourseExportImportProblem(CourseTestCase):
    """
    Tests for importing after exporting the course containing problem with pre tags from XML.
    """

    def setUp(self):
        super(TestCourseExportImportProblem, self).setUp()
        self.export_dir = tempfile.mkdtemp()
        self.source_course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        self.addCleanup(shutil.rmtree, self.export_dir, ignore_errors=True)

    def _setup_source_course_with_problem_content(self, data, publish_item=False):
        """
        Sets up course with problem content.
        """
        chapter = ItemFactory.create(
            parent_location=self.source_course.location,
            category='chapter',
            display_name='Test Section'
        )
        sequential = ItemFactory.create(
            parent_location=chapter.location,
            category='sequential',
            display_name='Test Sequential'
        )
        vertical = ItemFactory.create(
            category='vertical',
            parent_location=sequential.location,
            display_name='Test Unit'
        )

        ItemFactory.create(
            parent=vertical,
            category='problem',
            display_name='Test Problem',
            publish_item=publish_item,
            data=data,
        )

    def get_problem_content(self, block_location):
        """
        Get problem content of course.
        """
        if block_location.block_type == 'problem':
            return self.store.get_item(block_location).data

        return self.get_problem_content(self.store.get_item(block_location).children[0])

    def assert_problem_definition(self, course_location, expected_problem_content):
        """
        Asserts that problems' data is as expected with pre-tag content maintained.
        """
        problem_content = self.get_problem_content(course_location)
        self.assertEqual(expected_problem_content, problem_content)

    @ddt.data(
        [
            '<problem><pre><code>x=10 print("hello \n")</code></pre>'
            '<pre><div><pre><code>x=10 print("hello \n")</code></pre></div></pre>'
            '<multiplechoiceresponse></multiplechoiceresponse></problem>',

            '<problem>\n  <pre>\n    <code>x=10 print("hello \n")</code>\n  </pre>\n  <pre>\n    <div>\n      <pre>\n '
            '       <code>x=10 print("hello \n")</code>\n      </pre>\n    </div>\n  </pre>\n  '
            '<multiplechoiceresponse/>\n</problem>\n'
        ],
        [
            '<problem><pre><code>x=10 print("hello \n")</code></pre>'
            '<multiplechoiceresponse></multiplechoiceresponse></problem>',

            '<problem>\n  <pre>\n    <code>x=10 print("hello \n")</code>\n  </pre>\n  '
            '<multiplechoiceresponse/>\n</problem>\n'
        ]
    )
    @ddt.unpack
    def test_problem_content_on_course_export_import(self, problem_data, expected_problem_content):
        """
        Verify that problem content in destination matches expected problem content,
        specifically concerned with pre tag data with problem.
        """
        self._setup_source_course_with_problem_content(problem_data)

        dest_course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)

        export_course_to_xml(
            self.store,
            contentstore(),
            self.source_course.location.course_key,
            self.export_dir,
            'exported_source_course',
        )

        import_course_from_xml(
            self.store,
            self.user.id,
            self.export_dir,
            ['exported_source_course'],
            static_content_store=contentstore(),
            target_id=dest_course.location.course_key,
            load_error_modules=False,
            raise_on_failure=True,
            create_if_not_present=True,
        )

        self.assert_problem_definition(dest_course.location, expected_problem_content)
