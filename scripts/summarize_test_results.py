"""Summarize the results of running all the tests."""

import collections
import os

import click
from lxml import etree


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


def report_file(path, details):
    """Report on one nosetests.xml file."""
    print "\n{}".format(path)
    with open(path) as xml_file:
        tree = etree.parse(xml_file)                # pylint: disable=no-member
    suite = tree.xpath("/testsuite")[0]

    results = TestResults.from_element(suite)
    print results

    if details:
        errors = collections.Counter()
        for error_element in tree.xpath(".//error|.//failure"):
            errors[error_line_from_error_element(error_element)] += 1

        if errors:
            print ""
            for error_message, number in errors.most_common():
                print "{0:4d}: {1}".format(number, error_message)

    return results


@click.command()
@click.option("--details/--no-details", help="Show details of errors")
@click.argument("start", default="reports")
def report_all_files(details, start):
    """Find all the nosetests.xml files, and report on them."""
    totals = TestResults()
    for dirpath, _, filenames in os.walk(start):
        if "nosetests.xml" in filenames:
            results = report_file(os.path.join(dirpath, "nosetests.xml"), details=details)
            totals += results

    print "\nTotals:\n{}".format(totals)


if __name__ == "__main__":
    report_all_files()                  # pylint: disable=no-value-for-parameter
