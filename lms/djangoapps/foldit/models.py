import logging

from django.contrib.auth.models import User
from django.db import models


log = logging.getLogger(__name__)


class Score(models.Model):
    """
    This model stores the scores of different users on FoldIt problems.
    """
    user = models.ForeignKey(User, db_index=True,
                             related_name='foldit_scores')

    # The XModule that wants to access this doesn't have access to the real
    # userid.  Save the anonymized version so we can look up by that.
    unique_user_id = models.CharField(max_length=50, db_index=True)
    puzzle_id = models.IntegerField()
    best_score = models.FloatField(db_index=True)
    current_score = models.FloatField(db_index=True)
    score_version = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def display_score(score, sum_of=1):
        """
        Argument:
            score (float), as stored in the DB (i.e., "rosetta score")
            sum_of (int): if this score is the sum of scores of individual
               problems, how many elements are in that sum

        Returns:
            score (float), as displayed to the user in the game and in the leaderboard
        """
        return (-score) * 10 + 8000 * sum_of

    @staticmethod
    def get_tops_n(n, puzzles=['994559'], course_list=None):
        """
        Arguments:
            puzzles: a list of puzzle ids that we will use. If not specified,
            defaults to puzzle used in 7012x.
            n (int): number of top scores to return


        Returns:
            The top n sum of scores for puzzles in <puzzles>,
            filtered by course. If no courses is specified we default
            the pool of students to all courses. Output is a list
            of dictionaries, sorted by display_score:
                [ {username: 'a_user',
                   score: 12000} ...]
        """

        if not isinstance(puzzles, list):
            puzzles = [puzzles]
        if course_list is None:
            scores = Score.objects \
                .filter(puzzle_id__in=puzzles) \
                .annotate(total_score=models.Sum('best_score')) \
                .order_by('total_score')[:n]
        else:
            scores = Score.objects \
                .filter(puzzle_id__in=puzzles) \
                .filter(user__courseenrollment__course_id__in=course_list) \
                .annotate(total_score=models.Sum('best_score')) \
                .order_by('total_score')[:n]
        num = len(puzzles)

        return [
            {'username': score.user.username,
             'score': Score.display_score(score.total_score, num)}
            for score in scores
        ]


class PuzzleComplete(models.Model):
    """
    This keeps track of the sets of puzzles completed by each user.

    e.g. PuzzleID 1234, set 1, subset 3.  (Sets and subsets correspond to levels
    in the intro puzzles)
    """
    class Meta(object):  # pylint: disable=missing-docstring
        # there should only be one puzzle complete entry for any particular
        # puzzle for any user
        unique_together = ('user', 'puzzle_id', 'puzzle_set', 'puzzle_subset')
        ordering = ['puzzle_id']

    user = models.ForeignKey(User, db_index=True,
                             related_name='foldit_puzzles_complete')

    # The XModule that wants to access this doesn't have access to the real
    # userid.  Save the anonymized version so we can look up by that.
    unique_user_id = models.CharField(max_length=50, db_index=True)
    puzzle_id = models.IntegerField()
    puzzle_set = models.IntegerField(db_index=True)
    puzzle_subset = models.IntegerField(db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "PuzzleComplete({0}, id={1}, set={2}, subset={3}, created={4})".format(
            self.user.username, self.puzzle_id,
            self.puzzle_set, self.puzzle_subset,
            self.created)

    @staticmethod
    def completed_puzzles(anonymous_user_id):
        """
        Return a list of puzzles that this user has completed, as an array of
        dicts:

        [ {'set': int,
           'subset': int,
           'created': datetime} ]
        """
        complete = PuzzleComplete.objects.filter(unique_user_id=anonymous_user_id)
        return [{'set': c.puzzle_set,
                 'subset': c.puzzle_subset,
                 'created': c.created} for c in complete]

    @staticmethod
    def is_level_complete(anonymous_user_id, level, sub_level, due=None):
        """
        Return True if this user completed level--sub_level by due.

        Users see levels as e.g. 4-5.

        Args:
            level: int
            sub_level: int
            due (optional): If specified, a datetime.  Ignored if None.
        """
        complete = PuzzleComplete.objects.filter(unique_user_id=anonymous_user_id,
                                                 puzzle_set=level,
                                                 puzzle_subset=sub_level)
        if due is not None:
            complete = complete.filter(created__lte=due)

        return complete.exists()
