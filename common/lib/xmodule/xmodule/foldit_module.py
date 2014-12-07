import logging
from lxml import etree

from pkg_resources import resource_string

from xmodule.editing_module import EditingDescriptor
from xmodule.x_module import XModule
from xmodule.xml_module import XmlDescriptor
from xblock.fields import Scope, Integer, String
from .fields import Date


log = logging.getLogger(__name__)


class FolditFields(object):
    # default to what Spring_7012x uses
    required_level_half_credit = Integer(default=3, scope=Scope.settings)
    required_sublevel_half_credit = Integer(default=5, scope=Scope.settings)
    required_level = Integer(default=4, scope=Scope.settings)
    required_sublevel = Integer(default=5, scope=Scope.settings)
    due = Date(help="Date that this problem is due by", scope=Scope.settings)

    show_basic_score = String(scope=Scope.settings, default='false')
    show_leaderboard = String(scope=Scope.settings, default='false')


class FolditModule(FolditFields, XModule):

    css = {'scss': [resource_string(__name__, 'css/foldit/leaderboard.scss')]}

    def __init__(self, *args, **kwargs):
        """
        Example:
         <foldit show_basic_score="true"
            required_level="4"
            required_sublevel="3"
            required_level_half_credit="2"
            required_sublevel_half_credit="3"
            show_leaderboard="false"/>
        """
        super(FolditModule, self).__init__(*args, **kwargs)
        self.due_time = self.due

    def is_complete(self):
        """
        Did the user get to the required level before the due date?
        """
        # We normally don't want django dependencies in xmodule.  foldit is
        # special.  Import this late to avoid errors with things not yet being
        # initialized.
        from foldit.models import PuzzleComplete

        complete = PuzzleComplete.is_level_complete(
            self.system.anonymous_student_id,
            self.required_level,
            self.required_sublevel,
            self.due_time)
        return complete

    def is_half_complete(self):
        """
        Did the user reach the required level for half credit?

        Ideally this would be more flexible than just 0, 0.5, or 1 credit. On
        the other hand, the xml attributes for specifying more specific
        cut-offs and partial grades can get more confusing.
        """
        from foldit.models import PuzzleComplete
        complete = PuzzleComplete.is_level_complete(
            self.system.anonymous_student_id,
            self.required_level_half_credit,
            self.required_sublevel_half_credit,
            self.due_time)
        return complete

    def completed_puzzles(self):
        """
        Return a list of puzzles that this user has completed, as an array of
        dicts:

        [ {'set': int,
           'subset': int,
           'created': datetime} ]

        The list is sorted by set, then subset
        """
        from foldit.models import PuzzleComplete

        return sorted(
            PuzzleComplete.completed_puzzles(self.system.anonymous_student_id),
            key=lambda d: (d['set'], d['subset']))

    def puzzle_leaders(self, n=10, courses=None):
        """
        Returns a list of n pairs (user, score) corresponding to the top
        scores; the pairs are in descending order of score.
        """
        from foldit.models import Score

        if courses is None:
            courses = [self.location.course_key]

        leaders = [(leader['username'], leader['score']) for leader in Score.get_tops_n(10, course_list=courses)]
        leaders.sort(key=lambda x: -x[1])

        return leaders

    def get_html(self):
        """
        Render the html for the module.
        """
        goal_level = '{0}-{1}'.format(
            self.required_level,
            self.required_sublevel)

        showbasic = (self.show_basic_score.lower() == "true")
        showleader = (self.show_leaderboard.lower() == "true")

        context = {
            'due': self.due,
            'success': self.is_complete(),
            'goal_level': goal_level,
            'completed': self.completed_puzzles(),
            'top_scores': self.puzzle_leaders(),
            'show_basic': showbasic,
            'show_leader': showleader,
            'folditbasic': self.get_basicpuzzles_html(),
            'folditchallenge': self.get_challenge_html()
        }

        return self.system.render_template('foldit.html', context)

    def get_basicpuzzles_html(self):
        """
        Render html for the basic puzzle section.
        """
        goal_level = '{0}-{1}'.format(
            self.required_level,
            self.required_sublevel)

        context = {
            'due': self.due,
            'success': self.is_complete(),
            'goal_level': goal_level,
            'completed': self.completed_puzzles(),
        }
        return self.system.render_template('folditbasic.html', context)

    def get_challenge_html(self):
        """
        Render html for challenge (i.e., the leaderboard)
        """

        context = {
            'top_scores': self.puzzle_leaders()}

        return self.system.render_template('folditchallenge.html', context)

    def get_score(self):
        """
        0 if required_level_half_credit - required_sublevel_half_credit not
        reached.
        0.5 if required_level_half_credit and required_sublevel_half_credit
        reached.
        1 if requred_level and required_sublevel reached.
        """
        if self.is_complete():
            score = 1
        elif self.is_half_complete():
            score = 0.5
        else:
            score = 0
        return {'score': score,
                'total': self.max_score()}

    def max_score(self):
        return 1


class FolditDescriptor(FolditFields, XmlDescriptor, EditingDescriptor):
    """
    Module for adding Foldit problems to courses
    """
    mako_template = "widgets/html-edit.html"
    module_class = FolditModule
    filename_extension = "xml"

    has_score = True

    js = {'coffee': [resource_string(__name__, 'js/src/html/edit.coffee')]}
    js_module_name = "HTMLEditingDescriptor"

    # The grade changes without any student interaction with the edx website,
    # so always need to actually check.
    always_recalculate_grades = True

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        return {}, []

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('foldit')
        return xml_object
