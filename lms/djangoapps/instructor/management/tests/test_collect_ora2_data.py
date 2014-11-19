""" Test the collect_ora2_data management command """

from mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CollectOra2DataTest(ModuleStoreTestCase):
    """ Test collect_ora2_data output and error conditions """

    def setUp(self):
        self.course = CourseFactory.create()

        self.test_header = [
            "submission_uuid",
            "item_id",
            "anonymized_student_id",
            "submitted_at",
            "raw_answer",
            "assessments",
            "assessments_parts",
            "final_score_given_at",
            "final_score_points_earned",
            "final_score_points_possible",
            "feedback_options",
            "feedback",
        ]

        self.test_row = [
            [
                "33a639de-4e61-11e4-82ab-hash_value",
                "i4x://edX/DemoX/openassessment/hash_value",
                "e31b4beb3d191cd47b07e17735728d53",
                "2014-10-07 20:33:31+00:00",
                '{""text"": ""This is a response to a question. #dylan""}',
                "Assessment #1 -- scored_at: 2014-10-07 20:37:54 -- type: T -- scorer_id: hash -- feedback: Test",
                "Assessment #1 -- Content: Unclear recommendation (5)",
                "2014-10-07 21:35:47+00:00",
                "10",
                "20",
                "Completed test assessments.",
                "They were useful.",
            ]
        ]

    def test_invalid_course_key(self):
        """ Verify that management command raises exception for invalid or missing course """

        self.assertRaises(CommandError, call_command, ('collect_ora2_data',))
        self.assertRaises(CommandError, call_command, ('collect_ora2_data',), 'invalid_course_id')

    @patch('instructor.management.commands.collect_ora2_data.collect_ora2_data')
    def test_valid_data_output_to_file(self, mock_data):
        """ Verify that management command writes valid ORA2 data to file. """

        mock_data.return_value = (self.test_header, self.test_row)

        with patch('instructor.management.commands.collect_ora2_data.csv') as mock_write:
            call_command('collect_ora2_data', self.course.id.to_deprecated_string())

            mock_writerow = mock_write.writer.return_value.writerow

            mock_writerow.assert_any_call(self.test_header)
            mock_writerow.assert_called_with(self.test_row[0])

            mock_writerow.mock_calls = []

            call_command('collect_ora2_data', self.course.id)

            mock_writerow.assert_any_call(self.test_header)
            mock_writerow.assert_called_with(self.test_row[0])
