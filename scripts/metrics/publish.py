"""
Publish Build Stats.
"""

import os
import subprocess
from dogapi import dog_http_api
from coverage_metrics import CoverageMetrics


class PublishStats(object):
    """
    Publish stats to DataDog.
    """
    def __init__(self, api_key):
        dog_http_api.api_key = api_key

    @staticmethod
    def report_metrics(metrics):
        """
        Send metrics to DataDog.

        Arguments:
            metrics (dict): data to publish

        """
        for key, value in metrics.iteritems():
            print u"Sending {} ==> {}%".format(key, value)
            dog_http_api.metric(key, value)


def main(api_key):
    """
    Send Stats for everything to DataDog.
    """
    dir_path = os.path.dirname(os.path.relpath(__file__))

    unit_reports_cmd = ['find', 'reports', '-name', '"coverage.xml"']
    unit_report_paths = subprocess.check_output(unit_reports_cmd)

    cov_metrics = CoverageMetrics(os.path.join(dir_path, 'unit_test_groups.json'), unit_report_paths)
    coverage_metrics = cov_metrics.coverage_metrics()

    # Publish Coverage Stats to DataDog
    PublishStats(api_key).report_metrics(coverage_metrics)


if __name__ == "__main__":
    API_KEY = os.environ.get('DATADOG_API_KEY')
    if API_KEY:
        main(API_KEY)
    else:
        print 'SKIP: Publish Stats to Datadog'
