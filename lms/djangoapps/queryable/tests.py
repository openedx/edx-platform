"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from queryable import util


class TestUtil(TestCase):
    """
    Check the various utility functions.
    """

    def test_approx_equal(self):
        """
        Check that function testing for approximate equalality is working.
        """
        self.assertTrue(util.approx_equal(1.00001,1.0))
        self.assertTrue(util.approx_equal(1.0,1.00001))

        self.assertFalse(util.approx_equal(1.0,2.0))
        self.assertFalse(util.approx_equal(1.0,1.0002))

        self.assertTrue(util.approx_equal(1.0,1.0,1))
        self.assertTrue(util.approx_equal(1.0,1.000001,0.000001))

        self.assertFalse(util.approx_equal(1.0,2.0,0.75))
        self.assertFalse(util.approx_equal(2.0,1.0,0.75))

