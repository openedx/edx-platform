from nose.tools import assert_equals
from lxml import etree
from xmodule.stringify import stringify_children

def test_stringify():
    text = 'Hi <div x="foo">there <span>Bruce</span><b>!</b></div>'
    html = '''<html a="b" foo="bar">{0}</html>'''.format(text)
    xml = etree.fromstring(html)
    out = stringify_children(xml)
    assert_equals(out, text)
