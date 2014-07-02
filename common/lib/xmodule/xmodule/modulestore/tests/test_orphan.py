from xmodule.modulestore.tests.test_split_w_old_mongo import SplitWMongoCourseBoostrapper


class TestOrphan(SplitWMongoCourseBoostrapper):
    """
    Test the orphan finding code
    """

    def _create_course(self):
        """
        * some detached items
        * some attached children
        * some orphans
        """
        super(TestOrphan, self)._create_course()

        self._create_item('chapter', 'Chapter1', {}, {'display_name': 'Chapter 1'}, 'course', 'runid')
        self._create_item('chapter', 'Chapter2', {}, {'display_name': 'Chapter 2'}, 'course', 'runid')
        self._create_item('chapter', 'OrphanChapter', {}, {'display_name': 'Orphan Chapter'}, None, None)
        self._create_item('vertical', 'Vert1', {}, {'display_name': 'Vertical 1'}, 'chapter', 'Chapter1')
        self._create_item('vertical', 'OrphanVert', {}, {'display_name': 'Orphan Vertical'}, None, None)
        self._create_item('html', 'Html1', "<p>Goodbye</p>", {'display_name': 'Parented Html'}, 'vertical', 'Vert1')
        self._create_item('html', 'OrphanHtml', "<p>Hello</p>", {'display_name': 'Orphan html'}, None, None)
        self._create_item('static_tab', 'staticuno', "<p>tab</p>", {'display_name': 'Tab uno'}, None, None)
        self._create_item('about', 'overview', "<p>overview</p>", {}, None, None)
        self._create_item('course_info', 'updates', "<ol><li><h2>Sep 22</h2><p>test</p></li></ol>", {}, None, None)

    def test_mongo_orphan(self):
        """
        Test that old mongo finds the orphans
        """
        orphans = self.old_mongo.get_orphans(self.old_course_key)
        self.assertEqual(len(orphans), 3, "Wrong # {}".format(orphans))
        location = self.old_course_key.make_usage_key('chapter', 'OrphanChapter')
        self.assertIn(location.to_deprecated_string(), orphans)
        location = self.old_course_key.make_usage_key('vertical', 'OrphanVert')
        self.assertIn(location.to_deprecated_string(), orphans)
        location = self.old_course_key.make_usage_key('html', 'OrphanHtml')
        self.assertIn(location.to_deprecated_string(), orphans)

    def test_split_orphan(self):
        """
        Test that split mongo finds the orphans
        """
        orphans = self.split_mongo.get_orphans(self.split_course_key)
        self.assertEqual(len(orphans), 3, "Wrong # {}".format(orphans))
        location = self.split_course_key.make_usage_key('chapter', 'OrphanChapter')
        self.assertIn(location, orphans)
        location = self.split_course_key.make_usage_key('vertical', 'OrphanVert')
        self.assertIn(location, orphans)
        location = self.split_course_key.make_usage_key('html', 'OrphanHtml')
        self.assertIn(location, orphans)
