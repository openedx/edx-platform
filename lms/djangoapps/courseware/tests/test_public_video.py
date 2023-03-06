""" Tests for the public video view """
import ddt
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory
from lms.djangoapps.courseware.toggles import PUBLIC_VIDEO_SHARE


@ddt.ddt
class PublicVideoTests(ModuleStoreTestCase):
    """ Tests for the public video view """
    def setUp(self):
        super().setUp()
        self.course = CourseFactory()
        chapter = BlockFactory(parent=self.course, category='chapter')
        sequential = BlockFactory(parent=chapter, category='sequential')
        self.nonpublic_video = BlockFactory(parent=sequential, category='video', has_score=False, public_access=False)
        self.public_video = BlockFactory(parent=sequential, category='video', has_score=False, public_access=True)

    @ddt.unpack
    @ddt.data((True, True), (True, False), (False, True), (False, False))
    def test_access(self, is_waffle_enabled, is_public):
        """ Tests for acces control """
        target_video = self.public_video if is_public else self.nonpublic_video
        target_video_id = str(target_video.location)
        with override_waffle_flag(PUBLIC_VIDEO_SHARE, is_waffle_enabled):
            url = reverse('render_public_video_xblock', kwargs={'usage_key_string': target_video_id})
            resp = self.client.get(url)
        expected_status = 200 if is_waffle_enabled and is_public else 404
        self.assertEqual(expected_status, resp.status_code)
