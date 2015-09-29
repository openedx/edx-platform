#!/usr/bin/env python
"""Summarize the results of running all the tests.

See the report_all_files docstring for details, or run this with --help.

"""

import collections
import os

import click
from lxml import etree


@click.command()
@click.option(
    "--errors/--no-errors",
    help="Show details of errors and failures",
)
@click.option(
    "--names/--no-names",
    help=(
        "Show test names"
        " (with --errors, categorized by error message)"
    ),
)
@click.option(
    "--outcomes/--no-outcomes",
    help="Show pass/fail/error with names",
)
@click.argument(
    "start",
    default="reports",
)
def report_all_files(errors, names, outcomes, start):
    """Find all the nosetests.xml files, and report on them.

    For every nosetests.xml file found, prints a summary of the number of
    tests, fails, errors, etc.  If --details is used, then the error messages
    from all of the fails and errors will be shown, most frequent first, with a
    count of how many tests failed for that reason.

    """
    totals = TestResults()
    for dirpath, _, filenames in os.walk(start):
        if "nosetests.xml" in filenames:
            results = report_file(
                os.path.join(dirpath, "nosetests.xml"),
                errors=errors,
                names=names,
                outcomes=outcomes,
            )
            totals += results

    print "\nTotals:\n{}".format(totals)


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


def report_file(path, errors, names, outcomes):
    """Report on one nosetests.xml file."""
    print "\n{}".format(path)
    with open(path) as xml_file:
        tree = etree.parse(xml_file)                # pylint: disable=no-member
    suite = tree.xpath("/testsuite")[0]

    results = TestResults.from_element(suite)
    print results

    if errors:
        errors = collections.defaultdict(list)
        for error_element in tree.xpath(".//error|.//failure"):
            error_line = error_line_from_error_element(error_element)
            testcases = error_element.xpath("..")
            if testcases:
                testcase = testcases[0]
                errors[error_line].append(testcase_name(testcase))

        if errors:
            print ""
            errors = sorted(errors.items(), key=lambda kv: len(kv[1]), reverse=True)
            for error_message, test_names in errors:
                print "{0:4d}: {1}".format(len(test_names), error_message)
                if names:
                    for test_name in test_names:
                        print "        {}".format(test_name)

    elif names:
        for testcase in tree.xpath(".//testcase"):
            if outcomes:
                result = testcase.xpath("error|failure|skipped")
                if result:
                    outcome = result[0].tag[0].upper()
                else:
                    outcome = "."
            else:
                outcome = ""
            print "  {outcome} {testname}".format(
                outcome=outcome,
                testname=testcase_name(testcase),
            )

    return results


if __name__ == "__main__":
    report_all_files()                  # pylint: disable=no-value-for-parameter
