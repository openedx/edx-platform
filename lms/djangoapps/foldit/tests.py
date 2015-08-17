"""Tests for the FoldIt module"""
import json
import logging
from functools import partial

from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse

from foldit.views import foldit_ops, verify_code
from foldit.models import PuzzleComplete, Score
from student.models import unique_id_for_user, CourseEnrollment
from student.tests.factories import UserFactory

from datetime import datetime, timedelta
from pytz import UTC
from opaque_keys.edx.locations import SlashSeparatedCourseKey

log = logging.getLogger(__name__)


class FolditTestCase(TestCase):
    """Tests for various responses of the FoldIt module"""
    def setUp(self):
        super(FolditTestCase, self).setUp()

        self.factory = RequestFactory()
        self.url = reverse('foldit_ops')

        self.course_id = SlashSeparatedCourseKey('course', 'id', '1')
        self.course_id2 = SlashSeparatedCourseKey('course', 'id', '2')

        self.user = UserFactory.create()
        self.user2 = UserFactory.create()

        CourseEnrollment.enroll(self.user, self.course_id)
        CourseEnrollment.enroll(self.user2, self.course_id2)

        now = datetime.now(UTC)
        self.tomorrow = now + timedelta(days=1)
        self.yesterday = now - timedelta(days=1)

    def make_request(self, post_data, user=None):
        """Makes a request to foldit_ops with the given post data and user (if specified)"""
        request = self.factory.post(self.url, post_data)
        request.user = self.user if not user else user
        return request

    def make_puzzle_score_request(self, puzzle_ids, best_scores, user=None):
        """
        Given lists of puzzle_ids and best_scores (must have same length), make a
        SetPlayerPuzzleScores request and return the response.
        """
        if not isinstance(best_scores, list):
            best_scores = [best_scores]
        if not isinstance(puzzle_ids, list):
            puzzle_ids = [puzzle_ids]
        user = self.user if not user else user

        def score_dict(puzzle_id, best_score):
            """Returns a valid json-parsable score dict"""
            return {"PuzzleID": puzzle_id,
                    "ScoreType": "score",
                    "BestScore": best_score,
                    # current scores don't actually matter
                    "CurrentScore": best_score + 0.01,
                    "ScoreVersion": 23}
        scores = [score_dict(pid, bs) for pid, bs in zip(puzzle_ids, best_scores)]
        scores_str = json.dumps(scores)

        verify = {"Verify": verify_code(user.email, scores_str),
                  "VerifyMethod": "FoldItVerify"}
        data = {'SetPlayerPuzzleScoresVerify': json.dumps(verify),
                'SetPlayerPuzzleScores': scores_str}

        request = self.make_request(data, user)

        response = foldit_ops(request)
        self.assertEqual(response.status_code, 200)
        return response

    def test_SetPlayerPuzzleScores(self):  # pylint: disable=invalid-name

        puzzle_id = 994391
        best_score = 0.078034
        response = self.make_puzzle_score_request(puzzle_id, [best_score])

        self.assertEqual(response.content, json.dumps(
            [{"OperationID": "SetPlayerPuzzleScores",
              "Value": [{
                  "PuzzleID": puzzle_id,
                  "Status": "Success"}]}]))

        # There should now be a score in the db.
        top_10 = Score.get_tops_n(10, puzzle_id)
        self.assertEqual(len(top_10), 1)
        self.assertEqual(top_10[0]['score'], Score.display_score(best_score))

    def test_SetPlayerPuzzleScores_many(self):  # pylint: disable=invalid-name

        response = self.make_puzzle_score_request([1, 2], [0.078034, 0.080000])

        self.assertEqual(response.content, json.dumps(
            [{
                "OperationID": "SetPlayerPuzzleScores",
                "Value": [
                    {
                        "PuzzleID": 1,
                        "Status": "Success"
                    }, {
                        "PuzzleID": 2,
                        "Status": "Success"
                    }
                ]
            }]
        ))

    def test_SetPlayerPuzzleScores_multiple(self):  # pylint: disable=invalid-name
        """
        Check that multiple posts with the same id are handled properly
        (keep latest for each user, have multiple users work properly)
        """
        orig_score = 0.07
        puzzle_id = '1'
        self.make_puzzle_score_request([puzzle_id], [orig_score])

        # There should now be a score in the db.
        top_10 = Score.get_tops_n(10, puzzle_id)
        self.assertEqual(len(top_10), 1)
        self.assertEqual(top_10[0]['score'], Score.display_score(orig_score))

        # Reporting a better score should overwrite
        better_score = 0.06
        self.make_puzzle_score_request([1], [better_score])

        top_10 = Score.get_tops_n(10, puzzle_id)
        self.assertEqual(len(top_10), 1)

        # Floats always get in the way, so do almostequal
        self.assertAlmostEqual(
            top_10[0]['score'],
            Score.display_score(better_score),
            delta=0.5
        )

        # reporting a worse score shouldn't
        worse_score = 0.065
        self.make_puzzle_score_request([1], [worse_score])

        top_10 = Score.get_tops_n(10, puzzle_id)
        self.assertEqual(len(top_10), 1)
        # should still be the better score
        self.assertAlmostEqual(
            top_10[0]['score'],
            Score.display_score(better_score),
            delta=0.5
        )

    def test_SetPlayerPuzzleScores_multiple_courses(self):  # pylint: disable=invalid-name
        puzzle_id = "1"

        player1_score = 0.05
        player2_score = 0.06

        course_list_1 = [self.course_id]
        course_list_2 = [self.course_id2]

        self.make_puzzle_score_request(puzzle_id, player1_score, self.user)

        course_1_top_10 = Score.get_tops_n(10, puzzle_id, course_list_1)
        course_2_top_10 = Score.get_tops_n(10, puzzle_id, course_list_2)
        total_top_10 = Score.get_tops_n(10, puzzle_id)

        #  player1 should now be in the top 10 of course 1 and not in course 2
        self.assertEqual(len(course_1_top_10), 1)
        self.assertEqual(len(course_2_top_10), 0)
        self.assertEqual(len(total_top_10), 1)

        self.make_puzzle_score_request(puzzle_id, player2_score, self.user2)

        course_2_top_10 = Score.get_tops_n(10, puzzle_id, course_list_2)
        total_top_10 = Score.get_tops_n(10, puzzle_id)

        #  player2 should now be in the top 10 of course 2 and not in course 1
        self.assertEqual(len(course_1_top_10), 1)
        self.assertEqual(len(course_2_top_10), 1)
        self.assertEqual(len(total_top_10), 2)

    def test_SetPlayerPuzzleScores_many_players(self):  # pylint: disable=invalid-name
        """
        Check that when we send scores from multiple users, the correct order
        of scores is displayed. Note that, before being processed by
        display_score, lower scores are better.
        """
        puzzle_id = ['1']
        player1_score = 0.08
        player2_score = 0.02
        self.make_puzzle_score_request(puzzle_id, player1_score, self.user)

        # There should now be a score in the db.
        top_10 = Score.get_tops_n(10, puzzle_id)
        self.assertEqual(len(top_10), 1)
        self.assertEqual(top_10[0]['score'], Score.display_score(player1_score))

        self.make_puzzle_score_request(puzzle_id, player2_score, self.user2)

        # There should now be two scores in the db
        top_10 = Score.get_tops_n(10, puzzle_id)
        self.assertEqual(len(top_10), 2)

        # Top score should be player2_score. Second should be player1_score
        self.assertAlmostEqual(
            top_10[0]['score'],
            Score.display_score(player2_score),
            delta=0.5
        )
        self.assertAlmostEqual(
            top_10[1]['score'],
            Score.display_score(player1_score),
            delta=0.5
        )

        # Top score user should be self.user2.username
        self.assertEqual(top_10[0]['username'], self.user2.username)

    def test_SetPlayerPuzzleScores_error(self):  # pylint: disable=invalid-name

        scores = [{
            "PuzzleID": 994391,
            "ScoreType": "score",
            "BestScore": 0.078034,
            "CurrentScore": 0.080035,
            "ScoreVersion": 23
        }]
        validation_str = json.dumps(scores)

        verify = {
            "Verify": verify_code(self.user.email, validation_str),
            "VerifyMethod": "FoldItVerify"
        }

        # change the real string -- should get an error
        scores[0]['ScoreVersion'] = 22
        scores_str = json.dumps(scores)

        data = {
            'SetPlayerPuzzleScoresVerify': json.dumps(verify),
            'SetPlayerPuzzleScores': scores_str
        }

        request = self.make_request(data)

        response = foldit_ops(request)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content,
                         json.dumps([{
                             "OperationID": "SetPlayerPuzzleScores",
                             "Success": "false",
                             "ErrorString": "Verification failed",
                             "ErrorCode": "VerifyFailed"}]))

    def make_puzzles_complete_request(self, puzzles):
        """
        Make a puzzles complete request, given an array of
        puzzles.  E.g.

        [ {"PuzzleID": 13, "Set": 1, "SubSet": 2},
          {"PuzzleID": 53524, "Set": 1, "SubSet": 1} ]
        """
        puzzles_str = json.dumps(puzzles)

        verify = {
            "Verify": verify_code(self.user.email, puzzles_str),
            "VerifyMethod": "FoldItVerify"
        }

        data = {
            'SetPuzzlesCompleteVerify': json.dumps(verify),
            'SetPuzzlesComplete': puzzles_str
        }

        request = self.make_request(data)

        response = foldit_ops(request)
        self.assertEqual(response.status_code, 200)
        return response

    @staticmethod
    def set_puzzle_complete_response(values):
        """Returns a json response of a Puzzle Complete message"""
        return json.dumps([{"OperationID": "SetPuzzlesComplete",
                            "Value": values}])

    def test_SetPlayerPuzzlesComplete(self):  # pylint: disable=invalid-name

        puzzles = [
            {"PuzzleID": 13, "Set": 1, "SubSet": 2},
            {"PuzzleID": 53524, "Set": 1, "SubSet": 1}
        ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(response.content,
                         self.set_puzzle_complete_response([13, 53524]))

    def test_SetPlayerPuzzlesComplete_multiple(self):  # pylint: disable=invalid-name
        """Check that state is stored properly"""

        puzzles = [
            {"PuzzleID": 13, "Set": 1, "SubSet": 2},
            {"PuzzleID": 53524, "Set": 1, "SubSet": 1}
        ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(response.content,
                         self.set_puzzle_complete_response([13, 53524]))

        puzzles = [
            {"PuzzleID": 14, "Set": 1, "SubSet": 3},
            {"PuzzleID": 15, "Set": 1, "SubSet": 1}
        ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(
            response.content,
            self.set_puzzle_complete_response([13, 14, 15, 53524])
        )

    def test_SetPlayerPuzzlesComplete_level_complete(self):  # pylint: disable=invalid-name
        """Check that the level complete function works"""

        puzzles = [
            {"PuzzleID": 13, "Set": 1, "SubSet": 2},
            {"PuzzleID": 53524, "Set": 1, "SubSet": 1}
        ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(response.content,
                         self.set_puzzle_complete_response([13, 53524]))

        puzzles = [
            {"PuzzleID": 14, "Set": 1, "SubSet": 3},
            {"PuzzleID": 15, "Set": 1, "SubSet": 1}
        ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(response.content,
                         self.set_puzzle_complete_response([13, 14, 15, 53524]))

        is_complete = partial(
            PuzzleComplete.is_level_complete, unique_id_for_user(self.user))

        self.assertTrue(is_complete(1, 1))
        self.assertTrue(is_complete(1, 3))
        self.assertTrue(is_complete(1, 2))
        self.assertFalse(is_complete(4, 5))

        puzzles = [{"PuzzleID": 74, "Set": 4, "SubSet": 5}]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertTrue(is_complete(4, 5))

        # Now check due dates

        self.assertTrue(is_complete(1, 1, due=self.tomorrow))
        self.assertFalse(is_complete(1, 1, due=self.yesterday))

    def test_SetPlayerPuzzlesComplete_error(self):  # pylint: disable=invalid-name

        puzzles = [
            {"PuzzleID": 13, "Set": 1, "SubSet": 2},
            {"PuzzleID": 53524, "Set": 1, "SubSet": 1}
        ]

        puzzles_str = json.dumps(puzzles)

        verify = {
            "Verify": verify_code(self.user.email, puzzles_str + "x"),
            "VerifyMethod": "FoldItVerify"
        }

        data = {
            'SetPuzzlesCompleteVerify': json.dumps(verify),
            'SetPuzzlesComplete': puzzles_str
        }

        request = self.make_request(data)

        response = foldit_ops(request)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content,
                         json.dumps([{
                             "OperationID": "SetPuzzlesComplete",
                             "Success": "false",
                             "ErrorString": "Verification failed",
                             "ErrorCode": "VerifyFailed"}]))
