# -*- coding: utf-8 -*-
"""Test for License classes."""
import unittest
from xmodule.license import parse_license, License, ARRLicense, CCLicense


def assert_equal_license(self, left, right):
    self.assertEqual(left.kind, right.kind)
    if (not left.kind == "ARR" or not right.kind == "ARR"):
        self.assertEqual(left.version, right.version)


class LicenseTest(unittest.TestCase):
    """Tests for License class."""

    def setUp(self):
        self.noLicense = License()
        self.defaultLicense = ARRLicense()
        self.randomLicense = License('RAND', "v2.56")
        self.randomDict = {"kind": "RAND", "version": "v2.56"}
        self.randomDict2 = {"license": "RAND", "version": "v2.56"}
        self.invalidDict = {"kind": "RAND"}

    def test_html(self):
        """Should never be called in production, but otherwise say it's not licensed."""
        self.assertEqual(self.noLicense.html, u"<p>This resource is not licensed.</p>")

    def test_to_json(self):
        self.assertEqual(License().to_json(None)["kind"], "ARR")
        self.assertEqual(License().to_json(self.randomLicense), {"kind": "RAND", "version": "v2.56"})
        self.assertEqual(License().to_json(self.randomDict), {"kind": "RAND", "version": "v2.56"})
        with self.assertRaises(TypeError):
            License().to_json(self.invalidDict)

    def test_from_json(self):
        assert_equal_license(self, License().from_json(None), self.defaultLicense)
        assert_equal_license(self, License().from_json(""), self.defaultLicense)


class ARRLicenseTest(unittest.TestCase):
    """Tests for All Rights Reserved License class."""

    def setUp(self):
        self.arrLicense = ARRLicense()

    def test_html(self):
        self.assertEqual(self.arrLicense.html, "&copy;<span class='license-text'>All rights reserved</span>")

    def test_from_json(self):
        assert_equal_license(self, License().from_json("ARR"), self.arrLicense)


class CCLicenseTest(unittest.TestCase):
    """Tests for Creative Commons License class."""

    def setUp(self):
        self.cc0License = CCLicense("CC0")
        self.ccByLicense = CCLicense("CC-BY")
        self.ccBySaLicense = CCLicense("CC-BY-SA")
        self.ccByNdLicense = CCLicense("CC-BY-ND")
        self.ccByNcLicense = CCLicense("CC-BY-NC")
        self.ccByNcSaLicense = CCLicense("CC-BY-NC-SA")
        self.ccByNcNdLicense = CCLicense("CC-BY-NC-ND")

    def test_version(self):
        self.assertEqual(self.cc0License.version, "4.0")

    def test_html(self):
        # URL should be correct
        self.assertTrue("creativecommons.org/licenses/by-nc-sa/4.0/" in self.ccByNcSaLicense.html)

        # CC icon should be there
        self.assertTrue("class='icon-cc" in self.cc0License.html)

        # ZERO icon should be there
        self.assertTrue("icon-cc-zero" in self.cc0License.html)

        # BY icon should be there
        self.assertTrue("icon-cc-by" in self.ccByLicense.html)
        self.assertTrue("icon-cc-by" in self.ccBySaLicense.html)
        self.assertTrue("icon-cc-by" in self.ccByNdLicense.html)
        self.assertTrue("icon-cc-by" in self.ccByNcLicense.html)
        self.assertTrue("icon-cc-by" in self.ccByNcSaLicense.html)
        self.assertTrue("icon-cc-by" in self.ccByNcNdLicense.html)

        # NC icon should be there
        self.assertTrue("icon-cc-nc" in self.ccByNcLicense.html)
        self.assertTrue("icon-cc-nc" in self.ccByNcNdLicense.html)

        # SA icon should be there
        self.assertTrue("icon-cc-sa" in self.ccBySaLicense.html)
        self.assertTrue("icon-cc-sa" in self.ccByNcSaLicense.html)

        # ND icon should be there
        self.assertTrue("icon-cc-by" in self.ccByNdLicense.html)
        self.assertTrue("icon-cc-by" in self.ccByNcNdLicense.html)

    def test_from_json(self):
        assert_equal_license(self, License().from_json("CC0"), self.cc0License)
        assert_equal_license(self, License().from_json("CC-BY"), self.ccByLicense)
        assert_equal_license(self, License().from_json("CC-BY-SA"), self.ccBySaLicense)
        assert_equal_license(self, License().from_json("CC-BY-ND"), self.ccByNdLicense)
        assert_equal_license(self, License().from_json("CC-BY-NC"), self.ccByNcLicense)
        assert_equal_license(self, License().from_json("CC-BY-NC-SA"), self.ccByNcSaLicense)
        assert_equal_license(self, License().from_json("CC-BY-NC-ND"), self.ccByNcNdLicense)

    def test_description(self):
        # BY text should be there
        self.assertTrue("Attribution" in self.ccByLicense.description)
        self.assertTrue("Attribution" in self.ccBySaLicense.description)
        self.assertTrue("Attribution" in self.ccByNdLicense.description)
        self.assertTrue("Attribution" in self.ccByNcLicense.description)
        self.assertTrue("Attribution" in self.ccByNcSaLicense.description)
        self.assertTrue("Attribution" in self.ccByNcNdLicense.description)

        # NC text should be there
        self.assertTrue("NonCommercial" in self.ccByNcLicense.description)
        self.assertTrue("NonCommercial" in self.ccByNcNdLicense.description)

        # SA text should be there
        self.assertTrue("ShareAlike" in self.ccBySaLicense.description)
        self.assertTrue("ShareAlike" in self.ccByNcSaLicense.description)

        # ND text should be there
        self.assertTrue("NonDerivatives" in self.ccByNdLicense.description)
        self.assertTrue("NonDerivatives" in self.ccByNcNdLicense.description)


class ParseLicenseTest(unittest.TestCase):
    """Tests for license parser."""

    def test_parse_license(self):
        assert_equal_license(self, parse_license(None), ARRLicense())
        assert_equal_license(self, parse_license(""), ARRLicense())
        assert_equal_license(self, parse_license("ARR"), ARRLicense())
        assert_equal_license(self, parse_license("CC0"), CCLicense("CC0", "4.0"))
        assert_equal_license(self, parse_license("CC-BY"), CCLicense("CC-BY", "4.0"))
        assert_equal_license(self, parse_license({"license": "CC-BY", "version": "4.0"}), CCLicense("CC-BY", "4.0"))
        assert_equal_license(self, parse_license({"kind": "CC-BY", "version": "4.0"}), CCLicense("CC-BY", "4.0"))
        with self.assertRaises(ValueError):
            parse_license({"kind": "CC-BY"})
