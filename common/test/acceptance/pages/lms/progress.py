"""
Student progress page
"""


from common.test.acceptance.pages.lms.course_page import CoursePage


class ProgressPage(CoursePage):
    """
    Student progress page.
    """

    url_path = "progress"

    def is_browser_on_page(self):
        is_present = (
            self.q(css='.course-info').present and
            self.q(css='.grade-detail-graph').present
        )
        return is_present

    def x_tick_sr_text(self, tick_index):
        """
        Return an array of the sr text for a specific x-Axis tick on the
        progress chart.
        """
        selector = self.q(css='#grade-detail-graph .tickLabel')[tick_index]
        sr_fields = selector.find_elements_by_class_name('sr')
        return [field.text for field in sr_fields]

    def x_tick_label(self, tick_index):
        """
        Returns the label for the X-axis tick index,
        and a boolean indicating whether or not it is aria-hidden
        """
        selector = self.q(css='#grade-detail-graph .xAxis .tickLabel')[tick_index]
        tick_label = selector.find_elements_by_tag_name('span')[0]
        return [tick_label.text, tick_label.get_attribute('aria-hidden')]

    def y_tick_label(self, tick_index):
        """
        Returns the label for the Y-axis tick index,
        and a boolean indicating whether or not it is aria-hidden
        """
        selector = self.q(css='#grade-detail-graph .yAxis .tickLabel')[tick_index]
        tick_label = selector.find_elements_by_tag_name('span')[0]
        return [tick_label.text, tick_label.get_attribute('aria-hidden')]

    def graph_overall_score(self):
        """
        Returns the sr-only text for overall score on the progress chart,
        and the complete text for overall score (including the same sr-text).
        """
        selector = self.q(css='#grade-detail-graph .overallGrade')[0]
        label = selector.find_elements_by_class_name('sr')[0]
        return [label.text, selector.text]
