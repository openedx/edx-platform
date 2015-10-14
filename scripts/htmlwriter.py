"""
htmlwriter.py

$ python htmlwriter.py reports/ > test_summary.html

"""

import collections
import os
import sys
import textwrap
from xml.sax.saxutils import escape

from lxml import etree


class HtmlOutlineWriter(object):
    HEAD = textwrap.dedent(r"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8" />
        <style>
        html {
            font-family: sans-serif;
        }
        .toggle-box {
            display: none;
        }

        .toggle-box + label {
            cursor: pointer;
            display: block;
            line-height: 21px;
            margin-bottom: 5px;
        }

        .toggle-box + label + div {
            display: none;
            margin-bottom: 10px;
        }

        .toggle-box:checked + label + div {
            display: block;
        }

        .toggle-box + label:before {
            color: #888;
            content: "\25B8";
            display: block;
            float: left;
            height: 20px;
            line-height: 20px;
            margin-right: 5px;
            text-align: center;
            width: 20px;
        }

        .toggle-box:checked + label:before {
            content: "\25BE";
        }

        .error, .skipped {
            margin-left: 2em;
        }

        .count {
            font-weight: bold;
        }

        .test {
            margin-left: 2em;
        }

        .stdout {
            margin-left: 2em;
            font-family: Consolas, monospace;
        }
        </style>
        </head>
        <body>
    """)

    SECTION_START = textwrap.dedent(u"""\
        <div class="{klass}">
        <input class="toggle-box {klass}" id="sect_{id:05d}" type="checkbox">
        <label for="sect_{id:05d}">{html}</label>
        <div>
    """)

    SECTION_END = "</div></div>"

    def __init__(self, fout):
        self.fout = fout
        self.section_id = 0
        self.fout.write(self.HEAD)

    def start_section(self, html, klass=None):
        self.fout.write(self.SECTION_START.format(
            id=self.section_id, html=html, klass=klass or "",
        ).encode("utf8"))
        self.section_id += 1

    def end_section(self):
        self.fout.write(self.SECTION_END)

    def write(self, html):
        self.fout.write(html.encode("utf8"))


class Summable(object):
    """An object whose attributes can be added together easily.

    Subclass this and define `fields` on your derived class.

    """
    def __init__(self):
        for name in self.fields:
            setattr(self, name, 0)

    @classmethod
    def from_element(cls, element):
        """Construct a Summable from an xml element with the same attributes."""
        self = cls()
        for name in self.fields:
            setattr(self, name, int(element.get(name)))
        return self

    def __add__(self, other):
        result = type(self)()
        for name in self.fields:
            setattr(result, name, getattr(self, name) + getattr(other, name))
        return result


class TestResults(Summable):
    """A test result, makeable from a nosetests.xml <testsuite> element."""

    fields = ["tests", "errors", "failures", "skip"]

    def __str__(self):
        msg = "{0.tests:4d} tests, {0.errors} errors, {0.failures} failures, {0.skip} skipped"
        return msg.format(self)


def error_line_from_error_element(element):
    """Given an <error> element, get the important error line from it."""
    return element.get("message").splitlines()[0]


def testcase_name(testcase):
    """Given a <testcase> element, return the name of the test."""
    return "{classname}.{name}".format(
        classname=testcase.get("classname"),
        name=testcase.get("name"),
    )


def error_line_from_error_element(element):
    """Given an <error> element, get the important error line from it."""
    line = element.get("type")
    message_lines = element.get("message").splitlines()
    if message_lines:
        first_line = message_lines[0].strip()
    else:
        first_line = ""
    if first_line:
        line += ": " + first_line
    return line


def testcase_name(testcase):
    """Given a <testcase> element, return the name of the test."""
    return "{classname}.{name}".format(
        classname=testcase.get("classname"),
        name=testcase.get("name"),
    )


def clipped(text, maxlength=150):
    """Return the text, but at most `maxlength` characters."""
    if len(text) > maxlength:
        text = text[:maxlength-1] + u"\N{HORIZONTAL ELLIPSIS}"
    return text


def report_file(path, html_writer):
    """Report on one nosetests.xml file."""

    with open(path) as xml_file:
        tree = etree.parse(xml_file)                # pylint: disable=no-member
    suite = tree.xpath("/testsuite")[0]

    results = TestResults.from_element(suite)
    html = u'<span class="count">{number}:</span> {path}: {results}'.format(
        path=escape(path),
        results=results,
        number=results.errors+results.failures,
    )
    html_writer.start_section(html, klass="file")

    errors = collections.defaultdict(list)
    for element in tree.xpath(".//error|.//failure"):
        error_line = error_line_from_error_element(element)
        testcases = element.xpath("..")
        if testcases:
            errors[error_line].append(testcases[0])

    errors = sorted(errors.items(), key=lambda kv: len(kv[1]), reverse=True)
    for message, testcases in errors:
        html = u'<span class="count">{0:d}:</span> {1}'.format(len(testcases), escape(clipped(message)))
        html_writer.start_section(html, klass="error")
        for testcase in testcases:
            html_writer.start_section(escape(testcase_name(testcase)), klass="test")
            error_element = testcase.xpath("error|failure")[0]
            html_writer.write("""<pre class="stdout">""")
            html_writer.write(escape(error_element.get("message")))
            html_writer.write(u"\n"+escape(error_element.text))
            html_writer.write("</pre>")
            html_writer.end_section()
        html_writer.end_section()

    skipped = collections.defaultdict(list)
    for element in tree.xpath(".//skipped"):
        error_line = error_line_from_error_element(element)
        testcases = element.xpath("..")
        if testcases:
            skipped[error_line].append(testcases[0])

    if skipped:
        total = sum(len(v) for v in skipped.values())
        html_writer.start_section(u'<span class="count">{0:d}:</span> Skipped'.format(total), klass="skipped")
        skipped = sorted(skipped.items(), key=lambda kv: len(kv[1]), reverse=True)
        for message, testcases in skipped:
            html = u'<span class="count">{0:d}:</span> {1}'.format(len(testcases), escape(clipped(message)))
            html_writer.start_section(html, klass="error")
            for testcase in testcases:
                html_writer.write('<div>{}</div>'.format(escape(testcase_name(testcase))))
            html_writer.end_section()

        html_writer.end_section()

    html_writer.end_section()
    return results


def main(start):
    totals = TestResults()
    html_writer = HtmlOutlineWriter(sys.stdout)
    for dirpath, _, filenames in os.walk(start):
        if "xunit.xml" in filenames:
            results = report_file(os.path.join(dirpath, "xunit.xml"), html_writer)
            totals += results
    html_writer.write(escape(str(totals)))

def tryit():
    w = HtmlOutlineWriter(sys.stdout)
    for f in range(3):
        w.start_section("File foo{}.xml".format(f))
        w.write("this is about foo")
        for err in range(5):
            w.start_section("error {}".format(err))
            w.write("ugh")
            w.end_section()
        w.end_section()


if __name__ == "__main__":
    main(sys.argv[1])
