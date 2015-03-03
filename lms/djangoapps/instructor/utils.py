"""
Helpers for instructor app.
"""

from django import db

from xmodule.modulestore.django import modulestore

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module
from util.query import get_read_replica_cursor_if_available
from pymongo.errors import PyMongoError
from pymongo import MongoClient
from bson.son import SON
from datetime import date
from django.conf import settings
from django_comment_client.management_utils import get_mongo_connection_string

FORUMS_MONGO_PARAMS = settings.FORUM_MONGO_PARAMS


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


def collect_course_forums_data(course_id):
    """
    Given a SlashSeparatedCourseKey course_id, return headers and information
    related to course forums usage such as upvotes, downvotes, and number of posts
    """
    try:
        client = MongoClient(get_mongo_connection_string())
        mongodb = client[FORUMS_MONGO_PARAMS['database']]
        new_threads_query = generate_course_forums_query(course_id, "CommentThread")
        new_responses_query = generate_course_forums_query(course_id, "Comment", False)
        new_comments_query = generate_course_forums_query(course_id, "Comment", True)

        new_threads = mongodb.contents.aggregate(new_threads_query)['result']
        new_responses = mongodb.contents.aggregate(new_responses_query)['result']
        new_comments = mongodb.contents.aggregate(new_comments_query)['result']
    except PyMongoError:
        raise

    for entry in new_responses:
        entry['_id']['type'] = "Response"
    results = merge_join_course_forums(new_threads, new_responses, new_comments)
    parsed_results = [
        [
            "{0}-{1}-{2}".format(result['_id']['year'], result['_id']['month'], result['_id']['day']),
            result['_id']['type'],
            result['posts'],
            result['up_votes'],
            result['down_votes'],
            result['net_points'],
        ]
        for result in results
    ]
    header = ['Date', 'Type', 'Number', 'Up Votes', 'Down Votes', 'Net Points']
    return header, parsed_results


def merge_join_course_forums(threads, responses, comments):
    """
    Performs a merge of sorted threads, responses, comments data
    interleaving the results so the final result is in chronological order
    """
    data = []
    t_index, r_index, c_index = 0, 0, 0
    while (t_index < len(threads) or r_index < len(responses) or c_index < len(comments)):
        # checking out of bounds
        if t_index == len(threads):
            thread_date = date.max
        else:
            thread = threads[t_index]['_id']
            thread_date = date(thread["year"], thread["month"], thread["day"])
        if r_index == len(responses):
            response_date = date.max
        else:
            response = responses[r_index]["_id"]
            response_date = date(response["year"], response["month"], response["day"])
        if c_index == len(comments):
            comment_date = date.max
        else:
            comment = comments[c_index]["_id"]
            comment_date = date(comment["year"], comment["month"], comment["day"])

        if thread_date <= comment_date and thread_date <= response_date:
            data.append(threads[t_index])
            t_index += 1
            continue
        elif response_date <= thread_date and response_date <= comment_date:
            data.append(responses[r_index])
            r_index += 1
            continue
        else:
            data.append(comments[c_index])
            c_index += 1
    return data


def generate_course_forums_query(course_id, query_type, parent_id_check=None):
    """
    We can make one of 3 possible queries: CommentThread, Comment, or Response
    CommentThread is specified by _type
    Response, Comment are both _type="Comment". Comment differs in that it has a
    parent_id, so parent_id_check is set to True for Comments.
    """
    query = [
        {'$match': {
            'course_id': course_id.to_deprecated_string(),
            '_type': query_type,
        }},
        {'$project': {
            'year': {'$year': '$created_at'},
            'month': {'$month': '$created_at'},
            'day': {'$dayOfMonth': '$created_at'},
            'type': '$_type',
            'votes': '$votes',
        }},
        {'$group': {
            '_id': {
                'year': '$year',
                'month': '$month',
                'day': '$day',
                'type': '$type',
            },
            'posts': {"$sum": 1},
            'net_points': {'$sum': '$votes.point'},
            'up_votes': {'$sum': '$votes.up_count'},
            'down_votes': {'$sum': '$votes.down_count'},
        }},
        # order of the sort is important so we use SON
        {'$sort': SON([('_id.year', 1), ('_id.month', 1), ('_id.day', 1)])},
    ]
    if query_type == 'Comment':
        if parent_id_check is not None:
            query[0]['$match']['parent_id'] = {'$exists': parent_id_check}
    return query


def collect_ora2_data(course_id):
    """
    Query MySQL database for aggregated ora2 response data.
    """
    cursor = get_read_replica_cursor_if_available(db)

    #Syntax unsupported by other vendors such as SQLite test db
    if db.connection.vendor != 'mysql':
        return '', ['']

    raw_queries = ora2_data_queries().split(';')
    
    cursor.execute(raw_queries[0])
    cursor.execute(raw_queries[1], [course_id])

    header = [item[0] for item in cursor.description]

    return header, cursor.fetchall()


# pylint: disable=invalid-name
def ora2_data_queries():
    """
    Wraps a raw SQL query which retrieves all ORA2 responses for a course.
    """

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


def collect_student_forums_data(course_id):
    """
    Given a SlashSeparatedCourseKey course_id, return headers and information
    related to student forums usage
    """
    try:
        client = MongoClient(get_mongo_connection_string())
        mongodb = client[FORUMS_MONGO_PARAMS['database']]
        student_forums_query = generate_student_forums_query(course_id)
        results = mongodb.contents.aggregate(student_forums_query)['result']
    except PyMongoError:
        raise

    parsed_results = [
        [
            result['_id'],
            result['posts'],
            result['points'],
        ] for result in results
    ]
    header = ['Username', 'Posts', 'Points']
    return header, parsed_results


def generate_student_forums_query(course_id):
    """
    generates an aggregate query for student data which can be executed using pymongo
    :param course_id:
    :return: a list with dictionaries to fetch aggregate query for
    student forums data
    """
    query = [
        {
            "$match": {
                "course_id": course_id.to_deprecated_string(),
            }
        },

        {
            "$group": {
                "_id": "$author_username",
                "posts": {"$sum": 1},
                "points": {"$sum": "$votes.point"}
            }
        },
    ]
    return query
