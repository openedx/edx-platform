"""
Tests capa util
"""
import unittest

from . import test_capa_system
from capa.util import compare_with_tolerance, sanitize_html


class UtilTest(unittest.TestCase):
    """Tests for util"""
    def setUp(self):
        super(UtilTest, self).setUp()
        self.system = test_capa_system()

    def test_compare_with_tolerance(self):
        # Test default tolerance '0.001%' (it is relative)
        result = compare_with_tolerance(100.0, 100.0)
        self.assertTrue(result)
        result = compare_with_tolerance(100.001, 100.0)
        self.assertTrue(result)
        result = compare_with_tolerance(101.0, 100.0)
        self.assertFalse(result)
        # Test absolute percentage tolerance
        result = compare_with_tolerance(109.9, 100.0, '10%', False)
        self.assertTrue(result)
        result = compare_with_tolerance(110.1, 100.0, '10%', False)
        self.assertFalse(result)
        # Test relative percentage tolerance
        result = compare_with_tolerance(111.0, 100.0, '10%', True)
        self.assertTrue(result)
        result = compare_with_tolerance(112.0, 100.0, '10%', True)
        self.assertFalse(result)
        # Test absolute tolerance (string)
        result = compare_with_tolerance(109.9, 100.0, '10.0', False)
        self.assertTrue(result)
        result = compare_with_tolerance(110.1, 100.0, '10.0', False)
        self.assertFalse(result)
        # Test relative tolerance (string)
        result = compare_with_tolerance(111.0, 100.0, '0.1', True)
        self.assertTrue(result)
        result = compare_with_tolerance(112.0, 100.0, '0.1', True)
        self.assertFalse(result)
        # Test absolute tolerance (float)
        result = compare_with_tolerance(109.9, 100.0, 10.0, False)
        self.assertTrue(result)
        result = compare_with_tolerance(110.1, 100.0, 10.0, False)
        self.assertFalse(result)
        # Test relative tolerance (float)
        result = compare_with_tolerance(111.0, 100.0, 0.1, True)
        self.assertTrue(result)
        result = compare_with_tolerance(112.0, 100.0, 0.1, True)
        self.assertFalse(result)
        ##### Infinite values #####
        infinity = float('Inf')
        # Test relative tolerance (float)
        result = compare_with_tolerance(infinity, 100.0, 1.0, True)
        self.assertFalse(result)
        result = compare_with_tolerance(100.0, infinity, 1.0, True)
        self.assertFalse(result)
        result = compare_with_tolerance(infinity, infinity, 1.0, True)
        self.assertTrue(result)
        # Test absolute tolerance (float)
        result = compare_with_tolerance(infinity, 100.0, 1.0, False)
        self.assertFalse(result)
        result = compare_with_tolerance(100.0, infinity, 1.0, False)
        self.assertFalse(result)
        result = compare_with_tolerance(infinity, infinity, 1.0, False)
        self.assertTrue(result)
        # Test relative tolerance (string)
        result = compare_with_tolerance(infinity, 100.0, '1.0', True)
        self.assertFalse(result)
        result = compare_with_tolerance(100.0, infinity, '1.0', True)
        self.assertFalse(result)
        result = compare_with_tolerance(infinity, infinity, '1.0', True)
        self.assertTrue(result)
        # Test absolute tolerance (string)
        result = compare_with_tolerance(infinity, 100.0, '1.0', False)
        self.assertFalse(result)
        result = compare_with_tolerance(100.0, infinity, '1.0', False)
        self.assertFalse(result)
        result = compare_with_tolerance(infinity, infinity, '1.0', False)
        self.assertTrue(result)
        # Test absolute tolerance for smaller values
        result = compare_with_tolerance(100.01, 100.0, 0.01, False)
        self.assertTrue(result)
        result = compare_with_tolerance(100.001, 100.0, 0.001, False)
        self.assertTrue(result)
        result = compare_with_tolerance(100.01, 100.0, '0.01%', False)
        self.assertTrue(result)
        result = compare_with_tolerance(100.002, 100.0, 0.001, False)
        self.assertFalse(result)
        result = compare_with_tolerance(0.4, 0.44, 0.01, False)
        self.assertFalse(result)
        result = compare_with_tolerance(100.01, 100.0, 0.010, False)
        self.assertTrue(result)

        # Test complex_number instructor_complex
        result = compare_with_tolerance(0.4, complex(0.44, 0), 0.01, False)
        self.assertFalse(result)
        result = compare_with_tolerance(100.01, complex(100.0, 0), 0.010, False)
        self.assertTrue(result)
        result = compare_with_tolerance(110.1, complex(100.0, 0), '10.0', False)
        self.assertFalse(result)
        result = compare_with_tolerance(111.0, complex(100.0, 0), '10%', True)
        self.assertTrue(result)

    def test_sanitize_html(self):
        """
        Test for html sanitization with bleach.
        """
        allowed_tags = ['div', 'p', 'audio', 'pre', 'span']
        for tag in allowed_tags:
            queue_msg = "<{0}>Test message</{0}>".format(tag)
            self.assertEqual(sanitize_html(queue_msg), queue_msg)

        not_allowed_tag = 'script'
        queue_msg = "<{0}>Test message</{0}>".format(not_allowed_tag)
        expected = "&lt;script&gt;Test message&lt;/script&gt;"
        self.assertEqual(sanitize_html(queue_msg), expected)
