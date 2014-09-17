"""
Tests for the bulk settings page
"""
import unittest
from contentstore.tests.utils import CourseTestCase
from contentstore.utils import BulkSettingsUtil

from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory

from datetime import datetime
import random

@unittest.skip("Bulk Settings are currently disabled")
class BulkSettingsTests(CourseTestCase):
    """
    Redefine setting type constants for easier testing
    Also defined in contentstore.views.utilities.bulksettings,
    and these contstants must match those in contentestore.views.utilities.bulksettings.
    """

    UNIT_SETTING_TYPES = []
    PROBLEM_SETTING_TYPES = BulkSettingsUtil.PROBLEM_SETTING_TYPES
    COMPONENT_TYPES = BulkSettingsUtil.COMPONENT_TYPES
    SECTION_SETTING_TYPES = BulkSettingsUtil.SECTION_SETTING_TYPES
    SUBSECTION_SETTING_TYPES = BulkSettingsUtil.SUBSECTION_SETTING_TYPES
    CATEGORY_SETTING_MAP = BulkSettingsUtil.CATEGORY_SETTING_MAP
    NUM_RANDOM_TESTS = 10

    def setUp(self):
        """
        Set up initial data for testing.

        CourseTestCase's setUp initializes:
            - self.user: staff user
            - self.course
            - self.client
            - self.store
        """
        super(BulkSettingsTests, self).setUp()


    def populate_course_with_seed_data(self):
        """
        Populates the given course hierarchy with initial settings data
        Does tree expansion by x2 each level.
        """

        self.do_recursive_population(self.course, ['chapter', 'sequential', 'vertical', 'problem'])


    def do_recursive_population(self,parent, stack):
        block_category = stack.pop(0)
        for _ in range(2):
            child = self.create_item_of_category(block_category, parent)
            stack_copy = list(stack)
            if stack_copy:
                self.do_recursive_population(child, stack_copy)


    def create_item_of_category(self, category, parent):
        """
        Given a category and the parent, creates a block (item)
        and attaches it to the parent
        """
        metadata = {}
        setting_types = self.CATEGORY_SETTING_MAP[category]

        for setting_type in setting_types:
            metadata[setting_type] = self.generate_random_value_for(setting_type)

        item = ItemFactory.create(
            parent_location = parent.location,
            category = category,
            metadata = metadata
        )
        return item


    def generate_random_value_for(self, setting_type):
        """
        Given a setting type, (metadata attribute of a mixin class)
        generate a random value and return it.
        """

        randomization_values = ["Always", "On Reset", "Never", "Per Student"]
        show_answer_values = ["Always", "Answered", "Attempted", "Closed",
                                "Finished", "Past Due", "Never"]
        format_values = ["Quiz", "Homework"]

        if setting_type == "start" or setting_type == "due":
            return datetime.today()

        elif setting_type == "max_attempts":
            return random.randint(1, 10)

        elif setting_type == "weight" or setting_type == "submission_wait_seconds":
            return random.random() * 10

        elif setting_type == "rerandomize":
            return randomization_values[random.randint(0, 3)]
        elif setting_type == "showanswer":
            return show_answer_values[random.randint(0, 6)]
        else:
            return format_values[random.randint(0,1)]


    def test_empty_course(self):
        """
        Test that the computed settings data is empty when the course is empty.
        """
        empty_course = CourseFactory.create(
            org = 'edx',
            number = '999',
            display_name = 'test_course'
        )

        computed_settings_data = BulkSettingsUtil.get_bulksettings_metadata(empty_course)
        self.assertEqual(len(computed_settings_data), 0, msg="empty course should contain no settings")


    def test_empty_problem(self):
        """
        Test with no problems. If no unit holds any problems, the list should be empty.
        """
        empty_problem_course = CourseFactory.create(
            org = 'edx',
            number = '999',
            display_name = 'no_problem_course'
        )
        self.do_recursive_population(empty_problem_course, ['chapter', 'sequential', 'vertical'])
        computed_settings_data = BulkSettingsUtil.get_bulksettings_metadata(empty_problem_course)
        self.assertEqual(len(computed_settings_data), 0,
                        msg="course with no problem should yield no bulksettings")


    def test_multiple_bulksettings(self):
        """
        Do multiple tests with randomly generated settings data.

        Since this uses self.course, it attaches new xblock components to the same
        course every iteration, stress-testing with new random values.
        The number of xblocks that are added with each iteration is:
            2 + 4 + 8 + 16

        This is inteded to test both: 1) Large Courses + 2) Different values
        """

        for i in range(self.NUM_RANDOM_TESTS):
            self.test_bulksettings_data_correctness()


    def test_bulksettings_data_correctness(self):
        """
        Test that the populated course settings correctly match the result
        from _get_bulksettings_metadata.

        _get_bulksettings_metatdata is from contentstore.views.utilities.bulksettings

        Since the test populated course only contains problems, assume that indices
        match between computed settings & block.children

        Populate self.course with 2 chapters, 4 sections, 8 verticals, 16 problems
        and for each node, put in random settings
        """
        self.populate_course_with_seed_data()
        course_module = self.store.get_items(self.course.id, category='course')[0]
        computed_settings_data = BulkSettingsUtil.get_bulksettings_metadata(course_module)

        num_sections = len(computed_settings_data)
        sections = course_module.get_children()

        ''' Dive into the course hierarchy and check correct values.'''

        ''' Section Layer'''
        for index in range(num_sections):
            section = sections[index]
            computed_section_settings = computed_settings_data[index]
            self.assertTrue(self.do_values_match(self.SECTION_SETTING_TYPES,
                            section, computed_section_settings))

            num_subsections = len(section.get_children())

            ''' Subsection Layer '''
            for index in range(num_subsections):
                subsection = section.get_children()[index]
                computed_subsection_settings = computed_section_settings['children'][index]

                self.assertTrue(self.do_values_match(self.SUBSECTION_SETTING_TYPES,
                                subsection, computed_subsection_settings))

                num_units = len(subsection.get_children())

                ''' Unit Layer '''
                for index in range(num_units):
                    unit = subsection.get_children()[index]
                    num_components = len(unit.get_children())
                    computed_unit_settings = computed_subsection_settings['children'][index]

                    ''' Component Layer (Problems)'''
                    for index in range(num_components):
                        component = unit.get_children()[index]
                        computed_component_settings = computed_unit_settings['children'][index]
                        self.assertTrue(self.do_values_match(self.PROBLEM_SETTING_TYPES,
                                        component, computed_component_settings))


    def do_values_match(self, setting_types, child, computed_settings):
        """
        Checks if the actual settings of the given child matches
        the computed settings
        """

        for setting_type in setting_types:
            setting= getattr(child, setting_type)

            if setting_type == 'start' or setting_type == 'due':
                setting = setting.strftime('%m/%d/%Y')

            self.assertEqual(setting, computed_settings[setting_type],
                            msg="setting_type" + str(setting_type) + "does not match")
            if setting != computed_settings[setting_type]:
                return False

        return True


    def populate_settings(self):

        """
        For the chapters, sections, verticals, and problems in this course,
        put in random settings.
        """

        course_module = self.store.get_items(self.course.id, category='course')[0]
        for section in course_module.get_children():

            for setting_type in self.SECTION_SETTING_TYPES:
                setattr(section, setting_type, self.generate_random_value_for(setting_type))

            section.save()
            for subsection in section.get_children():

                for setting_type in self.SUBSECTION_SETTING_TYPES:
                    setattr(subsection, setting_type, self.generate_random_value_for(setting_type))
                subsection.save()

                for unit in subsection.get_children():

                    # All components are initialized as problems
                    for component in unit.get_children():
                        for setting_type in self.PROBLEM_SETTING_TYPES:
                            setattr(component, setting_type, self.generate_random_value_for(setting_type))
                        component.save()
        self.save_course()

