"""
Test the publish code (primary causing orphans)
"""
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.test_split_w_old_mongo import SplitWMongoCourseBoostrapper


class TestPublish(SplitWMongoCourseBoostrapper):
    """
    Test the publish code (primary causing orphans)
    """
    def _create_course(self):
        """
        Create the course, publish all verticals
        * some detached items
        """
        super(TestPublish, self)._create_course(split=False)

        self._create_item('chapter', 'Chapter1', {}, {'display_name': 'Chapter 1'}, 'course', 'runid', split=False)
        self._create_item('chapter', 'Chapter2', {}, {'display_name': 'Chapter 2'}, 'course', 'runid', split=False)
        self._create_item('vertical', 'Vert1', {}, {'display_name': 'Vertical 1'}, 'chapter', 'Chapter1', split=False)
        self._create_item('vertical', 'Vert2', {}, {'display_name': 'Vertical 2'}, 'chapter', 'Chapter1', split=False)
        self._create_item('html', 'Html1', "<p>Goodbye</p>", {'display_name': 'Parented Html'}, 'vertical', 'Vert1', split=False)
        self._create_item(
            'discussion', 'Discussion1',
            "discussion discussion_category=\"Lecture 1\" discussion_id=\"a08bfd89b2aa40fa81f2c650a9332846\" discussion_target=\"Lecture 1\"/>\n",
            {
                "discussion_category": "Lecture 1",
                "discussion_target": "Lecture 1",
                "display_name": "Lecture 1 Discussion",
                "discussion_id": "a08bfd89b2aa40fa81f2c650a9332846"
            },
            'vertical', 'Vert1',
            split=False
        )
        self._create_item('html', 'Html2', "<p>Hellow</p>", {'display_name': 'Hollow Html'}, 'vertical', 'Vert1', split=False)
        self._create_item(
            'discussion', 'Discussion2',
            "discussion discussion_category=\"Lecture 2\" discussion_id=\"b08bfd89b2aa40fa81f2c650a9332846\" discussion_target=\"Lecture 2\"/>\n",
            {
                "discussion_category": "Lecture 2",
                "discussion_target": "Lecture 2",
                "display_name": "Lecture 2 Discussion",
                "discussion_id": "b08bfd89b2aa40fa81f2c650a9332846"
            },
            'vertical', 'Vert2',
            split=False
        )
        self._create_item('static_tab', 'staticuno', "<p>tab</p>", {'display_name': 'Tab uno'}, None, None, split=False)
        self._create_item('about', 'overview', "<p>overview</p>", {}, None, None, split=False)
        self._create_item('course_info', 'updates', "<ol><li><h2>Sep 22</h2><p>test</p></li></ol>", {}, None, None, split=False)

    def _xmodule_recurse(self, item, action):
        """
        Applies action depth-first down tree and to item last.

        A copy of  cms.djangoapps.contentstore.views.helpers._xmodule_recurse to reproduce its use and behavior
        outside of django.
        """
        for child in item.get_children():
            self._xmodule_recurse(child, action)

        action(item)

    def test_publish_draft_delete(self):
        """
        To reproduce a bug (STUD-811) publish a vertical, convert to draft, delete a child, move a child, publish.
        See if deleted and moved children still is connected or exists in db (bug was disconnected but existed)
        """
        location = self.old_course_key.make_usage_key('vertical', name='Vert1')
        item = self.draft_mongo.get_item(location, 2)
        self._xmodule_recurse(
            item,
            lambda i: self.draft_mongo.publish(i.location, self.userid)
        )
        # verify status
        item = self.draft_mongo.get_item(location, 0)
        self.assertFalse(getattr(item, 'is_draft', False), "Item was published. Draft should not exist")
        # however, children are still draft, but I'm not sure that's by design

        # convert back to draft
        self.draft_mongo.convert_to_draft(location)
        # both draft and published should exist
        draft_vert = self.draft_mongo.get_item(location, 0)
        self.assertTrue(getattr(draft_vert, 'is_draft', False), "Item was converted to draft but doesn't say so")
        item = self.old_mongo.get_item(location, 0)
        self.assertFalse(getattr(item, 'is_draft', False), "Published item doesn't say so")

        # delete the discussion (which oddly is not in draft mode)
        location = self.old_course_key.make_usage_key('discussion', name='Discussion1')
        self.draft_mongo.delete_item(location)
        # remove pointer from draft vertical (verify presence first to ensure process is valid)
        self.assertIn(location, draft_vert.children)
        draft_vert.children.remove(location)
        # move the other child
        other_child_loc = self.old_course_key.make_usage_key('html', name='Html2')
        draft_vert.children.remove(other_child_loc)
        other_vert = self.draft_mongo.get_item(self.old_course_key.make_usage_key('vertical', name='Vert2'), 0)
        other_vert.children.append(other_child_loc)
        self.draft_mongo.update_item(draft_vert, self.userid)
        self.draft_mongo.update_item(other_vert, self.userid)
        # publish
        self._xmodule_recurse(
            draft_vert,
            lambda i: self.draft_mongo.publish(i.location, self.userid)
        )
        item = self.old_mongo.get_item(draft_vert.location, 0)
        self.assertNotIn(location, item.children)
        with self.assertRaises(ItemNotFoundError):
            self.draft_mongo.get_item(location)
        self.assertNotIn(other_child_loc, item.children)
        self.assertTrue(self.draft_mongo.has_item(other_child_loc), "Oops, lost moved item")
