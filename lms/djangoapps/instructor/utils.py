"""
Helpers for instructor app.
"""

from django import db

from xmodule.modulestore.django import modulestore

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module
from util.query import get_read_replica_cursor_if_available


class DummyRequest(object):
    """Dummy request"""

    META = {}

    def __init__(self):
        self.session = {}
        self.user = None
        return

    def get_host(self):
        """Return a default host."""
        return 'edx.mit.edu'

    def is_secure(self):
        """Always insecure."""
        return False


def get_module_for_student(student, usage_key, request=None):
    """Return the module for the (student, location) using a DummyRequest."""
    if request is None:
        request = DummyRequest()
        request.user = student

    descriptor = modulestore().get_item(usage_key, depth=0)
    field_data_cache = FieldDataCache([descriptor], usage_key.course_key, student)
    return get_module(student, request, usage_key, field_data_cache)


def collect_ora2_data(course_id):
    """
    Query MySQL database for aggregated ora2 response data.
    """
    cursor = get_read_replica_cursor_if_available(db)

    # Syntax unsupported by other vendors such as SQLite test db
    if db.connection.vendor != 'mysql':
        return '', ['']

    raw_queries = ora2_data_queries().split(';')

    cursor.execute(raw_queries[0])
    cursor.execute(raw_queries[1], [course_id])

    header = [item[0] for item in cursor.description]

    return header, cursor.fetchall()


def ora2_data_queries():
    """
    Wraps a raw SQL query which retrieves all ORA2 responses for a course.
    """

    # pylint: disable=invalid-name
    RAW_QUERY = """
SET SESSION group_concat_max_len = 1000000;
SELECT `sub`.`uuid` AS `submission_uuid`,
`student`.`item_id` AS `item_id`,
`student`.`student_id` AS `anonymized_student_id`,
`sub`.`submitted_at` AS `submitted_at`,
`sub`.`raw_answer` AS `raw_answer`,
(
    SELECT GROUP_CONCAT(
        CONCAT(
            "Assessment #", `assessment`.`id`,
            " -- scored_at: ", `assessment`.`scored_at`,
            " -- type: ", `assessment`.`score_type`,
            " -- scorer_id: ", `assessment`.`scorer_id`,
            IF(
                `assessment`.`feedback` != "",
                CONCAT(" -- overall_feedback: ", `assessment`.`feedback`),
                ""
            )
        )
        SEPARATOR '\n'
    )
    FROM `assessment_assessment` AS `assessment`
    WHERE `assessment`.`submission_uuid`=`sub`.`uuid`
    ORDER BY `assessment`.`scored_at` ASC
) AS `assessments`,
(
    SELECT GROUP_CONCAT(
        CONCAT(
            "Assessment #", `assessment`.`id`,
            " -- ", `criterion`.`label`,
            IFNULL(CONCAT(": ", `option`.`label`, " (", `option`.`points`, ")"), ""),
            IF(
                `assessment_part`.`feedback` != "",
                CONCAT(" -- feedback: ", `assessment_part`.`feedback`),
                ""
            )
        )
        SEPARATOR '\n'
    )
    FROM `assessment_assessment` AS `assessment`
    JOIN `assessment_assessmentpart` AS `assessment_part`
    ON `assessment_part`.`assessment_id`=`assessment`.`id`
    JOIN `assessment_criterion` AS `criterion`
    ON `criterion`.`id`=`assessment_part`.`criterion_id`
    LEFT JOIN `assessment_criterionoption` AS `option`
    ON `option`.`id`=`assessment_part`.`option_id`
    WHERE `assessment`.`submission_uuid`=`sub`.`uuid`
    ORDER BY `assessment`.`scored_at` ASC, `criterion`.`order_num` DESC
) AS `assessments_parts`,
(
    SELECT `created_at`
    FROM `submissions_score` AS `score`
    WHERE `score`.`submission_id`=`sub`.`id`
    ORDER BY `score`.`created_at` DESC LIMIT 1
) AS `final_score_given_at`,
(
    SELECT `points_earned`
    FROM `submissions_score` AS `score`
    WHERE `score`.`submission_id`=`sub`.`id`
    ORDER BY `score`.`created_at` DESC LIMIT 1
) AS `final_score_points_earned`,
(
    SELECT `points_possible`
    FROM `submissions_score` AS `score`
    WHERE `score`.`submission_id`=`sub`.`id`
    ORDER BY `score`.`created_at` DESC LIMIT 1
) AS `final_score_points_possible`,
(
    SELECT GROUP_CONCAT(`feedbackoption`.`text` SEPARATOR '\n')
    FROM `assessment_assessmentfeedbackoption` AS `feedbackoption`
    JOIN `assessment_assessmentfeedback_options` AS `feedback_join`
    ON `feedback_join`.`assessmentfeedbackoption_id`=`feedbackoption`.`id`
    JOIN `assessment_assessmentfeedback` AS `feedback`
    ON `feedback`.`id`=`feedback_join`.`assessmentfeedback_id`
    WHERE `feedback`.`submission_uuid`=`sub`.`uuid`
) AS `feedback_options`,
(
    SELECT `feedback_text`
    FROM `assessment_assessmentfeedback` as `feedback`
    WHERE `feedback`.`submission_uuid`=`sub`.`uuid`
    LIMIT 1
) AS `feedback`
FROM `submissions_submission` AS `sub`
JOIN `submissions_studentitem` AS `student` ON `sub`.`student_item_id`=`student`.`id`
WHERE `student`.`item_type`="openassessment" AND `student`.`course_id`=%s
    """

    return RAW_QUERY
