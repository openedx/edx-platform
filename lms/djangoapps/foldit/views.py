import hashlib
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from foldit.models import Score, PuzzleComplete
from student.models import unique_id_for_user

import re

log = logging.getLogger(__name__)


@login_required
@csrf_exempt
@require_POST
def foldit_ops(request):
    """
    Endpoint view for foldit operations.
    """
    responses = []
    if "SetPlayerPuzzleScores" in request.POST:
        puzzle_scores_json = request.POST.get("SetPlayerPuzzleScores")
        pz_verify_json = request.POST.get("SetPlayerPuzzleScoresVerify")
        log.debug("SetPlayerPuzzleScores message: puzzle scores: %r",
                  puzzle_scores_json)

        puzzle_score_verify = json.loads(pz_verify_json)
        if not verifies_ok(request.user.email,
                           puzzle_scores_json, puzzle_score_verify):
            responses.append({"OperationID": "SetPlayerPuzzleScores",
                              "Success": "false",
                              "ErrorString": "Verification failed",
                              "ErrorCode": "VerifyFailed"})
            log.warning(
                "Verification of SetPlayerPuzzleScores failed:"
                "user %s, scores json %r, verify %r",
                request.user,
                puzzle_scores_json,
                pz_verify_json
            )
        else:
            # This is needed because we are not getting valid json - the
            # value of ScoreType is an unquoted string. Right now regexes are
            # quoting the string, but ideally the json itself would be fixed.
            # To allow for fixes without breaking this, the regex should only
            # match unquoted strings,
            a = re.compile(r':([a-zA-Z]*),')
            puzzle_scores_json = re.sub(a, r':"\g<1>",', puzzle_scores_json)
            puzzle_scores = json.loads(puzzle_scores_json)
            responses.append(save_scores(request.user, puzzle_scores))

    if "SetPuzzlesComplete" in request.POST:
        puzzles_complete_json = request.POST.get("SetPuzzlesComplete")
        pc_verify_json = request.POST.get("SetPuzzlesCompleteVerify")

        log.debug("SetPuzzlesComplete message: %r",
                  puzzles_complete_json)

        puzzles_complete_verify = json.loads(pc_verify_json)

        if not verifies_ok(request.user.email,
                           puzzles_complete_json, puzzles_complete_verify):
            responses.append({"OperationID": "SetPuzzlesComplete",
                              "Success": "false",
                              "ErrorString": "Verification failed",
                              "ErrorCode": "VerifyFailed"})
            log.warning(
                "Verification of SetPuzzlesComplete failed:"
                " user %s, puzzles json %r, verify %r",
                request.user,
                puzzles_complete_json,
                pc_verify_json
            )
        else:
            puzzles_complete = json.loads(puzzles_complete_json)
            responses.append(save_complete(request.user, puzzles_complete))

    return HttpResponse(json.dumps(responses))


def verify_code(email, val):
    """
    Given the email and passed in value (str), return the expected
    verification code.
    """
    # TODO: is this the right string?
    verification_string = email.lower() + '|' + val
    return hashlib.md5(verification_string).hexdigest()


def verifies_ok(email, val, verification):
    """
    Check that the hash_str matches the expected hash of val.

    Returns True if verification ok, False otherwise
    """
    if verification.get("VerifyMethod") != "FoldItVerify":
        log.debug("VerificationMethod in %r isn't FoldItVerify", verification)
        return False
    hash_str = verification.get("Verify")

    return verify_code(email, val) == hash_str


def save_scores(user, puzzle_scores):
    score_responses = []
    for score in puzzle_scores:
        log.debug("score: %s", score)
        # expected keys ScoreType, PuzzleID (int),
        # BestScore (energy), CurrentScore (Energy), ScoreVersion (int)

        puzzle_id = score['PuzzleID']
        best_score = score['BestScore']
        current_score = score['CurrentScore']
        score_version = score['ScoreVersion']

        # SetPlayerPuzzleScoreResponse object
        # Score entries are unique on user/unique_user_id/puzzle_id/score_version
        try:
            obj = Score.objects.get(
                user=user,
                unique_user_id=unique_id_for_user(user),
                puzzle_id=puzzle_id,
                score_version=score_version)
            obj.current_score = current_score
            obj.best_score = best_score

        except Score.DoesNotExist:
            obj = Score(
                user=user,
                unique_user_id=unique_id_for_user(user),
                puzzle_id=puzzle_id,
                current_score=current_score,
                best_score=best_score,
                score_version=score_version)
        obj.save()

        score_responses.append({'PuzzleID': puzzle_id,
                                'Status': 'Success'})

    return {"OperationID": "SetPlayerPuzzleScores", "Value": score_responses}


def save_complete(user, puzzles_complete):
    """
    Returned list of PuzzleIDs should be in sorted order (I don't think client
    cares, but tests do)
    """
    for complete in puzzles_complete:
        log.debug("Puzzle complete: %s", complete)
        puzzle_id = complete['PuzzleID']
        puzzle_set = complete['Set']
        puzzle_subset = complete['SubSet']

        # create if not there
        PuzzleComplete.objects.get_or_create(
            user=user,
            unique_user_id=unique_id_for_user(user),
            puzzle_id=puzzle_id,
            puzzle_set=puzzle_set,
            puzzle_subset=puzzle_subset)

    # List of all puzzle ids of intro-level puzzles completed ever, including on this
    # request
    # TODO: this is just in this request...

    complete_responses = list(pc.puzzle_id
                              for pc in PuzzleComplete.objects.filter(user=user))

    return {"OperationID": "SetPuzzlesComplete", "Value": complete_responses}
