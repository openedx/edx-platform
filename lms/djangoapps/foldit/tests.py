import json
import logging
from functools import partial

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings
from django.core.urlresolvers import reverse

from foldit.views import foldit_ops, verify_code
from foldit.models import PuzzleComplete
from student.models import UserProfile, unique_id_for_user

from datetime import datetime, timedelta

log = logging.getLogger(__name__)


class FolditTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse('foldit_ops')

        pwd = 'abc'
        self.user = User.objects.create_user('testuser', 'test@test.com', pwd)
        self.unique_user_id = unique_id_for_user(self.user)
        now = datetime.now()
        self.tomorrow = now + timedelta(days=1)
        self.yesterday = now - timedelta(days=1)

        UserProfile.objects.create(user=self.user)

    def make_request(self, post_data):
        request = self.factory.post(self.url, post_data)
        request.user = self.user
        return request

    def test_SetPlayerPuzzleScores(self):

        scores = [ {"PuzzleID": 994391,
                    "ScoreType": "score",
                    "BestScore": 0.078034,
                    "CurrentScore":0.080035,
                    "ScoreVersion":23}]
        scores_str = json.dumps(scores)

        verify = {"Verify": verify_code(self.user.email, scores_str),
                  "VerifyMethod":"FoldItVerify"}
        data = {'SetPlayerPuzzleScoresVerify': json.dumps(verify),
                'SetPlayerPuzzleScores': scores_str}

        request = self.make_request(data)

        response = foldit_ops(request)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, json.dumps(
            [{"OperationID": "SetPlayerPuzzleScores",
              "Value": [{
                  "PuzzleID": 994391,
                  "Status": "Success"}]}]))


    def test_SetPlayerPuzzleScores_many(self):

        scores = [ {"PuzzleID": 994391,
                    "ScoreType": "score",
                    "BestScore": 0.078034,
                    "CurrentScore":0.080035,
                    "ScoreVersion":23},

                    {"PuzzleID": 994392,
                    "ScoreType": "score",
                    "BestScore": 0.078000,
                    "CurrentScore":0.080011,
                    "ScoreVersion":23}]

        scores_str = json.dumps(scores)

        verify = {"Verify": verify_code(self.user.email, scores_str),
                  "VerifyMethod":"FoldItVerify"}
        data = {'SetPlayerPuzzleScoresVerify': json.dumps(verify),
                'SetPlayerPuzzleScores': scores_str}

        request = self.make_request(data)

        response = foldit_ops(request)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, json.dumps(
            [{"OperationID": "SetPlayerPuzzleScores",
              "Value": [{
                  "PuzzleID": 994391,
                  "Status": "Success"},

                  {"PuzzleID": 994392,
                  "Status": "Success"}]}]))



    def test_SetPlayerPuzzleScores_error(self):

        scores = [ {"PuzzleID": 994391,
                    "ScoreType": "score",
                    "BestScore": 0.078034,
                    "CurrentScore":0.080035,
                    "ScoreVersion":23}]
        validation_str = json.dumps(scores)

        verify = {"Verify": verify_code(self.user.email, validation_str),
                  "VerifyMethod":"FoldItVerify"}

        # change the real string -- should get an error
        scores[0]['ScoreVersion'] = 22
        scores_str = json.dumps(scores)

        data = {'SetPlayerPuzzleScoresVerify': json.dumps(verify),
                'SetPlayerPuzzleScores': scores_str}

        request = self.make_request(data)

        response = foldit_ops(request)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)

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

        verify = {"Verify": verify_code(self.user.email, puzzles_str),
                  "VerifyMethod":"FoldItVerify"}

        data =  {'SetPuzzlesCompleteVerify': json.dumps(verify),
                'SetPuzzlesComplete': puzzles_str}

        request = self.make_request(data)

        response = foldit_ops(request)
        self.assertEqual(response.status_code, 200)
        return response

    @staticmethod
    def set_puzzle_complete_response(values):
        return json.dumps([{"OperationID":"SetPuzzlesComplete",
                            "Value": values}])


    def test_SetPlayerPuzzlesComplete(self):

        puzzles = [ {"PuzzleID": 13, "Set": 1, "SubSet": 2},
                    {"PuzzleID": 53524, "Set": 1, "SubSet": 1} ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(response.content,
                         self.set_puzzle_complete_response([13, 53524]))



    def test_SetPlayerPuzzlesComplete_multiple(self):
        """Check that state is stored properly"""

        puzzles = [ {"PuzzleID": 13, "Set": 1, "SubSet": 2},
                    {"PuzzleID": 53524, "Set": 1, "SubSet": 1} ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(response.content,
                         self.set_puzzle_complete_response([13, 53524]))

        puzzles = [ {"PuzzleID": 14, "Set": 1, "SubSet": 3},
                    {"PuzzleID": 15, "Set": 1, "SubSet": 1} ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(response.content,
                         self.set_puzzle_complete_response([13, 14, 15, 53524]))



    def test_SetPlayerPuzzlesComplete_level_complete(self):
        """Check that the level complete function works"""

        puzzles = [ {"PuzzleID": 13, "Set": 1, "SubSet": 2},
                    {"PuzzleID": 53524, "Set": 1, "SubSet": 1} ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(response.content,
                         self.set_puzzle_complete_response([13, 53524]))

        puzzles = [ {"PuzzleID": 14, "Set": 1, "SubSet": 3},
                    {"PuzzleID": 15, "Set": 1, "SubSet": 1} ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertEqual(response.content,
                         self.set_puzzle_complete_response([13, 14, 15, 53524]))

        is_complete = partial(
            PuzzleComplete.is_level_complete, self.unique_user_id)

        self.assertTrue(is_complete(1, 1))
        self.assertTrue(is_complete(1, 3))
        self.assertTrue(is_complete(1, 2))
        self.assertFalse(is_complete(4, 5))

        puzzles = [ {"PuzzleID": 74, "Set": 4, "SubSet": 5} ]

        response = self.make_puzzles_complete_request(puzzles)

        self.assertTrue(is_complete(4, 5))

        # Now check due dates

        self.assertTrue(is_complete(1, 1, due=self.tomorrow))
        self.assertFalse(is_complete(1, 1, due=self.yesterday))



    def test_SetPlayerPuzzlesComplete_error(self):

        puzzles = [ {"PuzzleID": 13, "Set": 1, "SubSet": 2},
                    {"PuzzleID": 53524, "Set": 1, "SubSet": 1} ]

        puzzles_str = json.dumps(puzzles)

        verify = {"Verify": verify_code(self.user.email, puzzles_str + "x"),
                  "VerifyMethod":"FoldItVerify"}

        data = {'SetPuzzlesCompleteVerify': json.dumps(verify),
                'SetPuzzlesComplete': puzzles_str}

        request = self.make_request(data)

        response = foldit_ops(request)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)

        self.assertEqual(response.content,
                         json.dumps([{
                             "OperationID": "SetPuzzlesComplete",
                             "Success": "false",
                             "ErrorString": "Verification failed",
                             "ErrorCode": "VerifyFailed"}]))
