import logging
from lxml import etree
from dateutil import parser

from pkg_resources import resource_string

from xmodule.editing_module import EditingDescriptor
from xmodule.x_module import XModule
from xmodule.xml_module import XmlDescriptor

log = logging.getLogger(__name__)

class FolditModule(XModule):
    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
                         instance_state, shared_state, **kwargs)
        # ooh look--I'm lazy, so hardcoding the 7.00x required level.
        # If we need it generalized, can pull from the xml later
        self.required_level = 4
        self.required_sublevel = 5

        def parse_due_date():
            """
            Pull out the date, or None
            """
            s = self.metadata.get("due")
            if s:
                return parser.parse(s)
            else:
                return None

        self.due_str = self.metadata.get("due", "None")
        self.due = parse_due_date()

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
            self.due)
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


    def get_html(self):
        """
        Render the html for the module.
        """
        goal_level = '{0}-{1}'.format(
            self.required_level,
            self.required_sublevel)

        context = {
            'due': self.due_str,
            'success': self.is_complete(),
            'goal_level': goal_level,
            'completed': self.completed_puzzles(),
            }

        return self.system.render_template('foldit.html', context)


    def get_score(self):
        """
        0 / 1 based on whether student has gotten far enough.
        """
        score = 1 if self.is_complete() else 0
        return {'score': score,
                'total': self.max_score()}

    def max_score(self):
        return 1


class FolditDescriptor(XmlDescriptor, EditingDescriptor):
    """
    Module for adding open ended response questions to courses
    """
    mako_template = "widgets/html-edit.html"
    module_class = FolditModule
    filename_extension = "xml"

    stores_state = True
    has_score = True
    template_dir_name = "foldit"

    js = {'coffee': [resource_string(__name__, 'js/src/html/edit.coffee')]}
    js_module_name = "HTMLEditingDescriptor"

    # The grade changes without any student interaction with the edx website,
    # so always need to actually check.
    always_recalculate_grades = True

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        For now, don't need anything from the xml
        """
        return {}
