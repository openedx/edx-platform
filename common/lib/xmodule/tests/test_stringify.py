from nose.tools import assert_equals
from lxml import etree
from stringify import stringify_children

def test_stringify():
    html = '''<html a="b" foo="bar">Hi <div x="foo">there <span>Bruce</span><b>!</b></div></html>'''
    xml = etree.fromstring(html)
    out = stringify_children(xml)
    assert_equals(out, '''Hi <div x="foo">there <span>Bruce</span><b>!</b></div>''')
