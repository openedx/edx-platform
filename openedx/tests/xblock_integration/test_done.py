'''
Tests for the DoneXBlock.

This is nice as a simple example of the edX XBlock test framework.
'''

from openedx.tests.xblock_integration.xblock_testcase import XBlockTestCase


# pylint: disable=abstract-method
class TestDone(XBlockTestCase):
    """
    Simple tests for the completion XBlock. We set up a page with two
    of the block, make sure the page renders, toggle them a few times,
    make sure they've toggled, and reconfirm the page renders.
    """

    olx_scenarios = {  # Currently not used
        "two_done_block_test_case": """<vertical>
          <done urlname="done0"/>
          <done urlname="done1"/>
        </vertical>"""
    }

    # This is a stop-gap until we can load OLX and/or OLX from
    # normal workbench scenarios
    test_configuration = [
        {
            "urlname": "two_done_block_test_case_0",
            #"olx": self.olx_scenarios[0],
            "xblocks": [  # Stopgap until we handle OLX
                {
                    'blocktype': 'done',
                    'urlname': 'done_0'
                }
            ]
        },
        {
            "urlname": "two_done_block_test_case_1",
            #"olx": self.olx_scenarios[0],
            "xblocks": [  # Stopgap until we handle OLX
                {
                    'blocktype': 'done',
                    'urlname': 'done_1'
                }
            ]
        }
    ]

    def toggle_button(self, block, data, desired_state):
        """
        Make an AJAX call to the XBlock, and assert the state is as
        desired.
        """
        resp = self.ajax('toggle_button', block, data)
        self.assertEqual(resp.status_code, 200)
        # pylint: disable=no-member
        self.assertEqual(resp.data, {"state": desired_state})

    # pylint: disable=unused-argument
    def check_response(self, block_urlname, rendering):
        """
        Confirm that we have a 200 response code (no server error)

        In the future, visual diff test the response.
        """
        response = self.render_block(block_urlname)
        self.assertEqual(response.status_code, 200)
        # To do: Below method needs to be implemented
        #self.assertXBlockScreenshot(block_urlname, rendering)

    def test_done(self):
        """
        Walk through a few toggles. Make sure the blocks don't mix up
        state between them, initial state is correct, and final state
        is correct.
        """
        # We confirm we don't have errors rendering the student view
        self.check_response('done_0', 'done-unmarked')
        self.check_response('done_1', 'done-unmarked')

        # We confirm the block is initially false
        self.toggle_button('done_0', {}, False)
        self.reset_published_events()
        self.toggle_button('done_1', {}, False)
        self.assert_no_events_published("edx.done.toggled")

        # We confirm we can toggle state both ways
        self.reset_published_events()
        self.toggle_button('done_0', {'done': True}, True)
        self.assert_event_published('edx.done.toggled', event_fields={"done": True})
        self.reset_published_events()
        self.toggle_button('done_1', {'done': False}, False)
        self.assert_event_published('edx.done.toggled', event_fields={"done": False})
        self.toggle_button('done_0', {'done': False}, False)
        self.assert_grade(0)
        self.toggle_button('done_1', {'done': True}, True)
        self.assert_grade(1)

        # We confirm state sticks around
        self.toggle_button('done_0', {}, False)
        self.toggle_button('done_1', {}, True)

        # And confirm we render correctly
        self.check_response('done_0', 'done-unmarked')
        self.check_response('done_1', 'done-marked')
