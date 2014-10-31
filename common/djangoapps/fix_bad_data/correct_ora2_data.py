"""
    Created to fix a scoring problem caused by a bug in ORA2. This is a fix to mitigate
    the affects of that bug. (edx/edx-ora2#628)
    
    Fixes submission_score.points_earned for records affected by the track changes bug.
    Updates submission_scoresummary as a reult of this.
    Updates assessment_trackchanges.edited_content with a message from the course staff.
    
    To run this, create a file of TrackChanges ID's (see read_file method) and run the 
    "correct_ora2_scores" method from the command line.
"""

import logging

from openassessment.assessment.models.base import Assessment
from openassessment.assessment.api.peer import get_assessment_median_scores
from submissions.models import Submission, Score
from openassessment.assessment.models.trackchanges import TrackChanges
from openassessment.assessment.models.peer import PeerWorkflowItem

logger = logging.getLogger(__name__)


def read_file():
    """
    Read file containing id's of affected TrackChanges items
    
    File should be named 'track_changes' and be of the format of a row for each id (no trailing commas)
    
    Return:
        - list of id's
    """
    
    track_changes_file = open('track_changes')
    return track_changes_file.readlines()

def update_edited_content(track_change):
    """
    Prepend informational string to the edited content
    """
    
    information_string = """
                            <p>Message from the course staff:</p>
                            <p>This submission may have been incorrectly scored, due to a system error related to this assessment.</p>
                            <p> This assessment will now be discounted, provided that doing so will not lower your score.</p>
                            <p>End of Message.</p>
                            <p></p>
                          """

    track_change.edited_content = ''.join([information_string, track_change.edited_content])
    track_change.save()
    
    logger.info((
        u"TrackChanges.edited_content for id {id} has been prepended with course staff message."
    ).format(id=track_change.id))

def change_scored_flag(submission_uuid, scorer_id):
    """
    Changes PeerWorkflowItem.scored to 0 if:
        - scored = 1

    Input:
        - submission_uuid
        - scorer_id
    """
    assessment = Assessment.objects.get(submission_uuid=submission_uuid, scorer_id=scorer_id)

    try:
        peer_workflow_item = PeerWorkflowItem.objects.get(submission_uuid=submission_uuid, assessment_id=assessment.id, scored=1)
        peer_workflow_item.scored = 0
        peer_workflow_item.save()

        msg = (
            u"PeerWorkflowItem.scored for submission_UUID {uuid}, assessment ID {assessment_id} has been updated from 1 to 0"
        ).format(uuid=submission_uuid, assessment_id=assessment.id)

    except PeerWorkflowItem.DoesNotExist:
        msg = (
            u"Could not retrieve PeerWorkflowItem for submission_UUID {uuid}, assessment ID {assessment_id}"
        ).format(uuid=submission_uuid, assessment_id=assessment.id)

    logger.info(msg)

def generate_score(owner_submission_uuid):
    """
    Calculates the score of the submission using existing ORA2 api

    Input:
        - owner_submission_uuid
    Return:
        - Actual score to be stored in Score.points_earned
    """
    median_score_dict = get_assessment_median_scores(owner_submission_uuid)
    return sum(median_score_dict.values())

def get_submissions_score(owner_submission_uuid):
    """
    Gets the existing score for the submission
    
    Input:
        - owner_submission_uuid
    """
    submission_score = Score.objects.select_related('submission').filter(submission__uuid=owner_submission_uuid)[0]
    points_earned = submission_score.points_earned
    return points_earned

def update_score(owner_submission_uuid, new_generated_score, points_earned):
    """"
    Updates the score for the submission from points_earned to new_generated_score
    
    Automagically, ScoreSummary is also updated with the highest and latest
    
    Input:
        - owner_submission_uuid
        - new_generated_score
        - points_earned
    """
    if new_generated_score > points_earned:
        submission_score = Score.objects.select_related('submission').filter(submission__uuid=owner_submission_uuid)[0]
        submission_score.points_earned = new_generated_score
        submission_score.save()
        
        msg = (
            u"Score.points_earned for submission UUID {uuid} has been updated from {points_earned} to {new_generated_score}"
        ).format(uuid=owner_submission_uuid, new_generated_score=new_generated_score, points_earned=points_earned)
    else:
        msg = (
            u"Score not updated for submission_UUID {uuid}"
        ).format(uuid=owner_submission_uuid)
        
    logger.info(msg)

def correct_ora2_scores():
    """
    Fix up the ora2 scores affected by ORA2 bug (see top of file)". Also, update the assessment edited content with a message
    informing the student of this action.
    
    Spreadsheet of track changes items affected by the bug: 
    https://docs.google.com/spreadsheets/d/1IumfVAJohQeKd-KLuaL8D0gjczucy0uA4U_LiWgxmeE/edit#gid=1739770575
    
    The list below was taken from the above spreadsheet.
    """

    # Read id's from file
    track_changes_id_list = read_file()

    track_changes = TrackChanges.objects.filter(id__in = track_changes_id_list)

    for track_change in track_changes:
        owner_submission_uuid = track_change.owner_submission_uuid
        scorer_id = track_change.scorer_id
        
        # Change the scored flag on associated PeerWorkflowItem to 0
        # so it is not considered in the score calculation
        change_scored_flag(owner_submission_uuid, scorer_id)

        # Get the existing score for this submission
        try:
            points_earned = get_submissions_score(owner_submission_uuid)
        except IndexError:
            continue

        # Calculate new score; PeerWorkflowItems with scored=0 are not considered
        new_generated_score = generate_score(owner_submission_uuid)

        # Only update the score if the new score is > old score
        update_score(owner_submission_uuid, new_generated_score, points_earned)

        # Update edited_content regardless of whether the score was changed
        update_edited_content(track_change)
