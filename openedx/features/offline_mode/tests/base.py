"""
Tests for the testing xBlock renderers for Offline Mode.
"""

from xmodule.capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory


class CourseForOfflineTestCase(ModuleStoreTestCase):
    """
    Base class for creation course for Offline Mode testing.
    """

    def setUp(self):
        super().setUp()
        default_store = self.store.default_modulestore.get_modulestore_type()
        with self.store.default_store(default_store):
            self.course = CourseFactory.create(  # lint-amnesty, pylint: disable=attribute-defined-outside-init
                display_name='Offline Course',
                org='RaccoonGang',
                number='1',
                run='2024',
            )
            chapter = BlockFactory.create(parent=self.course, category='chapter')
            problem_xml = MultipleChoiceResponseXMLFactory().build_xml(
                question_text='The correct answer is Choice 2',
                choices=[False, False, True, False],
                choice_names=['choice_0', 'choice_1', 'choice_2', 'choice_3']
            )
            self.vertical_block = BlockFactory.create(  # lint-amnesty, pylint: disable=attribute-defined-outside-init
                parent_location=chapter.location,
                category='vertical',
                display_name='Vertical'
            )
            self.html_block = BlockFactory.create(  # lint-amnesty, pylint: disable=attribute-defined-outside-init
                parent=self.vertical_block,
                category='html',
                display_name='HTML xblock for Offline',
                data='<p>Test HTML Content<p>'
            )
            self.problem_block = BlockFactory.create(  # lint-amnesty, pylint: disable=attribute-defined-outside-init
                parent=self.vertical_block,
                category='problem',
                display_name='Problem xblock for Offline',
                data=problem_xml
            )
