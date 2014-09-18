# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from nose.tools import assert_equals, assert_greater  # pylint: disable=E0611


@step(u'I should see the following links and ids')
def should_see_a_link_called(step):
    for link_id_pair in step.hashes:
        link_id = link_id_pair['id']
        text = link_id_pair['Link']
        link = world.browser.find_by_id(link_id)
        assert_greater(
            len(link),
            0,
            "Link length is less than 1. ID: {id} Text: {text}".format(id=link_id, text=text)
        )
        assert_equals(link.text, text)
