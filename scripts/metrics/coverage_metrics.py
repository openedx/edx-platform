"""
Aggregate coverage data from XML reports.

groups.json is a JSON-encoded dict mapping group names to source file glob patterns:
{
    "group_1": "group1/*.py",
    "group_2": "group2/*.py"
}

This would calculate line coverage percentages for source files in each group,
and send those metrics to DataDog:

testeng.coverage.group_1 ==> 89.123
testeng.coverage.group_2 ==> 45.523

The tool uses the *union* of covered lines across each of the input
coverage XML reports.  If a line is covered *anywhere*, it's considered covered.
"""

import fnmatch
import json
from lxml import etree


class CoverageParseError(Exception):
    """
    Error occurred while parsing a coverage report.
    """
    pass


class CoverageData(object):
    """
    Aggregate coverage reports.
    """

    def __init__(self):
        """
        Initialize the coverage data, which has no information until you add a report.
        """
        self._coverage = dict()

    def add_report(self, report_str):
        """
        Add the coverage information from the XML `report_str` to the aggregate data.
        Raises a `CoverageParseError` if the report XML is not a valid coverage report.
        """
        try:
            root = etree.fromstring(report_str)

        except etree.XMLSyntaxError:
            raise CoverageParseError("Warning: Could not parse report as XML")

        if root is not None:

            # Get all classes (source files) in the report
            for class_node in root.xpath('//class'):

                class_filename = class_node.get('filename')

                if class_filename is None:
                    continue

                # If we haven't seen this source file before, create a dict
                # to store its coverage information.
                if class_filename not in self._coverage:
                    self._coverage[class_filename] = dict()

                # Store info for each line in the source file
                for line in class_node.xpath('lines/line'):

                    hits = line.get('hits')
                    line_num = line.get('number')

                    # Ignore lines that do not have the right attributes
                    if line_num is not None:

                        try:
                            line_num = int(line_num)
                            hits = int(hits)

                        except ValueError:
                            pass

                        else:

                            # If any report says the line is covered, set it to covered
                            if hits > 0:
                                self._coverage[class_filename][line_num] = 1

                            # Otherwise if the line is not already covered, set it to uncovered
                            elif line_num not in self._coverage[class_filename]:
                                self._coverage[class_filename][line_num] = 0

    def coverage(self, source_pattern="*"):
        """
        Calculate line coverage percentage (float) for source files that match
        `source_pattern` (a fnmatch-style glob pattern).

        If coverage could not be calculated (e.g. because no source files match
        the pattern), returns None.
        """
        num_covered = 0
        total = 0

        # Find source files that match the pattern then calculate total lines and number covered
        for filename in fnmatch.filter(self._coverage.keys(), source_pattern):
            num_covered += sum(self._coverage[filename].values())
            total += len(self._coverage[filename])

        # Calculate the percentage
        if total > 0:
            return float(num_covered) / float(total) * 100.0

        else:
            print u"Warning: No lines found in source files that match {}".format(source_pattern)
            return None

    @staticmethod
    def _parse_report(report_path):
        """
        Parse the coverage report as XML and return the resulting tree.
        If the report could not be found or parsed, return None.
        """
        try:
            return etree.parse(report_path)

        except IOError:
            print u"Warning: Could not open report at '{path}'".format(path=report_path)
            return None

        except ValueError:
            print u"Warning: Could not parse report at '{path}' as XML".format(path=report_path)
            return None


class CoverageMetrics(object):
    """
    Collect Coverage Reports for DataDog.
    """

    def __init__(self, group_json_path, report_paths):
        self._group_json_path = group_json_path
        self._report_paths = report_paths

    def coverage_metrics(self):
        """
        Find, parse, and create coverage metrics to be sent to DataDog.
        """
        print "Loading group definitions..."
        group_dict = self.load_group_defs(self._group_json_path)

        print "Parsing reports..."
        metrics = self.parse_reports(self._report_paths)

        print "Creating metrics..."
        stats = self.create_metrics(metrics, group_dict)
        print "Done."

        return stats

    @staticmethod
    def load_group_defs(group_json_path):
        """
        Load the dictionary mapping group names to source file patterns
        from the file located at `group_json_path`.

        Exits with an error message if the groups could not be parsed.
        """
        try:
            with open(group_json_path) as json_file:
                return json.load(json_file)

        except IOError:
            print u"Could not open group definition file at '{}'".format(group_json_path)
            raise

        except ValueError:
            print u"Could not parse group definitions in '{}'".format(group_json_path)
            raise

    @staticmethod
    def parse_reports(report_paths):
        """
        Parses each coverage report in `report_paths` and returns
        a `CoverageData` object containing the aggregate coverage information.
        """
        data = CoverageData()

        for path in report_paths:

            try:
                with open(path) as report_file:
                    data.add_report(report_file.read())

            except IOError:
                print u"Warning: could not open {}".format(path)

            except CoverageParseError:
                print u"Warning: could not parse {} as an XML coverage report".format(path)

        return data

    @staticmethod
    def create_metrics(data, groups):
        """
        Given a `CoverageData` object, create coverage percentages for each group.

        `groups` is a dict mapping aggregate group names to source file patterns.
        Group names are used in the name of the metric sent to DataDog.
        """
        metrics = {}
        for group_name, pattern in groups.iteritems():
            metric = 'test_eng.coverage.{group}'.format(group=group_name.replace(' ', '_'))
            percent = data.coverage(pattern)

            if percent is not None:
                print u"Sending {} ==> {}%".format(metric, percent)
                metrics[metric] = percent

        return metrics
