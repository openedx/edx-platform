from nose.tools import assert_equals  # pylint: disable=E0611
from lxml import etree
from xmodule.stringify import stringify_children


def test_stringify():
    expected = 'Hi <div x="foo">there <span>Bruce</span><b>!</b></div>'
    html = '''<html a="b" foo="bar">{0}</html>'''.format(expected)
    xml = etree.fromstring(html)
    actual = stringify_children(xml)
    assert_equals(actual, expected)


def test_stringify_again():
    html = r"""<html name="Voltage Source Answer" >A voltage source is non-linear!
<div align="center">
    <img src="/static/images/circuits/voltage-source.png"/>
    \(V=V_C\)
  </div>
  But it is <a href="http://mathworld.wolfram.com/AffineFunction.html">affine</a>,
  which means linear except for an offset.
  </html>
"""
    expected = r"""A voltage source is non-linear!
<div align="center">
    <img src="/static/images/circuits/voltage-source.png"/>
    \(V=V_C\)
  </div>
  But it is <a href="http://mathworld.wolfram.com/AffineFunction.html">affine</a>,
  which means linear except for an offset.
  """
    xml = etree.fromstring(html)
    actual = stringify_children(xml)
    assert_equals(actual, expected)
