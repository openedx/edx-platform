from eventtracking import tracker
from lms.djangoapps.instructor_task.models import ReportStore
from util.file import course_filename_prefix_generator
from edxmako.shortcuts import render_to_string

import waffle


REPORT_REQUESTED_EVENT_NAME = u'edx.instructor.report.requested'

# define value to use when no task_id is provided:
UNKNOWN_TASK_ID = 'unknown-task_id'

# define values for update functions to use to return status to perform_module_state_update
UPDATE_STATUS_SUCCEEDED = 'succeeded'
UPDATE_STATUS_FAILED = 'failed'
UPDATE_STATUS_SKIPPED = 'skipped'


def upload_csv_to_report_store(rows, csv_name, course_id, timestamp, config_name='GRADES_DOWNLOAD'):
    """
    Upload data as a CSV using ReportStore.

    Arguments:
        rows: CSV data in the following format (first column may be a
            header):
            [
                [row1_colum1, row1_colum2, ...],
                ...
            ]
        csv_name: Name of the resulting CSV
        course_id: ID of the course

    Returns:
        report_name: string - Name of the generated report
    """
    report_store = ReportStore.from_config(config_name)
    report_name = u"{course_prefix}_{csv_name}_{timestamp_str}.csv".format(
        course_prefix=course_filename_prefix_generator(course_id),
        csv_name=csv_name,
        timestamp_str=timestamp.strftime("%Y-%m-%d-%H%M")
    )

    disclaimer = SensitiveMessageOnReports()
    if disclaimer.should_msg_be_displayed:
        # Append the new row above the headers.
        send_disclaimer = disclaimer.with_report_store()
        rows = [send_disclaimer] + rows

    report_store.store_rows(course_id, report_name, rows)
    tracker_emit(csv_name)
    return report_name


def tracker_emit(report_name):
    """
    Emits a 'report.requested' event for the given report.
    """
    tracker.emit(REPORT_REQUESTED_EVENT_NAME, {"report_type": report_name, })


class SensitiveMessageOnReports(object):
    """
    Adds a sensitive data message to the reports if the waffle switch
    display_sensitive_data_msg_for_downloads is enabled.

    Due to reports being generated in different ways, each one handles their own way:
        1. Using the CSV library directly.
        2. Using upload_csv_to_report_store function which in turn
           uses store_rows of DjangoStorageReportStore class where is built the CSV.
    """

    def __init__(self):
        self.should_msg_be_displayed = waffle.switch_is_active('display_sensitive_data_msg_for_downloads')

    def csv_direct(self, writer):
        """
        Writes the row immediately in the CSV.
        """
        if self.should_msg_be_displayed:
            msg = self.process_message()
            encode = unicode(msg).encode('utf-8')
            writer.writerow([encode])

    def with_report_store(self):
        """
        Return the string parsed in process_message. This string is passed
        to upload_csv_to_report_store which decides if execute it or not.
        """
        return [self.process_message()]

    def process_message(self):
        """
        Return the message parsed from template.
        """
        template_message = 'instructor/instructor_dashboard_2/sensitive_data_download_msg.txt'
        message = render_to_string(template_message, None)
        return message
