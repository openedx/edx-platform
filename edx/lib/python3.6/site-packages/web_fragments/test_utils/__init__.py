"""
Test utilities.
"""

from __future__ import absolute_import, unicode_literals

TEST_HTML = '<p>Hello, world!</p>'
TEST_CSS = 'body {background-color:red;}'
TEST_CSS_URL = '/css/test.css'
TEST_JS = 'window.alert("Hello");'
TEST_JS_URL = '/js/test.js'
TEST_JS_INIT_FN = 'mock_initialize'
TEST_JSON_INIT_ARGS = {'test_value': 1}

CSS_EXPECTED_HTML = "<style type='text/css'>{css}</style>"
CSS_LINK_EXPECTED_HTML = "<link rel='stylesheet' href='{css_url}' type='text/css'>"
JS_EXPECTED_HTML = "<script>{js}</script>"
JS_LINK_EXPECTED_HTML = "<script src='{js_url}' type='application/javascript'></script>"
