"""Test of models for embargo middleware app"""
from django.test import TestCase

from xmodule.modulestore.locations import SlashSeparatedCourseKey
from embargo.models import EmbargoedCourse, EmbargoedState, IPFilter


class EmbargoModelsTest(TestCase):
    """Test each of the 3 models in embargo.models"""
    def test_course_embargo(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        # Test that course is not authorized by default
        self.assertFalse(EmbargoedCourse.is_embargoed(course_id))

        # Authorize
        cauth = EmbargoedCourse(course_id=course_id, embargoed=True)
        cauth.save()

        # Now, course should be embargoed
        self.assertTrue(EmbargoedCourse.is_embargoed(course_id))
        self.assertEquals(
            cauth.__unicode__(),
            "Course 'abc/123/doremi' is Embargoed"
        )

        # Unauthorize by explicitly setting email_enabled to False
        cauth.embargoed = False
        cauth.save()
        # Test that course is now unauthorized
        self.assertFalse(EmbargoedCourse.is_embargoed(course_id))
        self.assertEquals(
            cauth.__unicode__(),
            "Course 'abc/123/doremi' is Not Embargoed"
        )

    def test_state_embargo(self):
        # Azerbaijan and France should not be blocked
        good_states = ['AZ', 'FR']
        # Gah block USA and Antartica
        blocked_states = ['US', 'AQ']
        currently_blocked = EmbargoedState.current().embargoed_countries_list

        for state in blocked_states + good_states:
            self.assertFalse(state in currently_blocked)

        # Block
        cauth = EmbargoedState(embargoed_countries='US, AQ')
        cauth.save()
        currently_blocked = EmbargoedState.current().embargoed_countries_list

        for state in good_states:
            self.assertFalse(state in currently_blocked)
        for state in blocked_states:
            self.assertTrue(state in currently_blocked)

        # Change embargo - block Isle of Man too
        blocked_states.append('IM')
        cauth.embargoed_countries = 'US, AQ, IM'
        cauth.save()
        currently_blocked = EmbargoedState.current().embargoed_countries_list

        for state in good_states:
            self.assertFalse(state in currently_blocked)
        for state in blocked_states:
            self.assertTrue(state in currently_blocked)

    def test_ip_blocking(self):
        whitelist = '127.0.0.1'
        blacklist = '18.244.51.3'

        cwhitelist = IPFilter.current().whitelist_ips
        self.assertFalse(whitelist in cwhitelist)
        cblacklist = IPFilter.current().blacklist_ips
        self.assertFalse(blacklist in cblacklist)

        IPFilter(whitelist=whitelist, blacklist=blacklist).save()

        cwhitelist = IPFilter.current().whitelist_ips
        self.assertTrue(whitelist in cwhitelist)
        cblacklist = IPFilter.current().blacklist_ips
        self.assertTrue(blacklist in cblacklist)
