"""
Student progress page
"""

from bok_choy.page_object import PageObject
from . import BASE_URL


class ProgressPage(PageObject):
    """
    Student progress page.
    """

    name = "lms.progress"

    def url(self, course_id=None):  #pylint: disable=W0221
        return BASE_URL + "/courses/" + course_id + "/progress"

    def is_browser_on_page(self):
        has_course_info = self.is_css_present('section.course-info')
        has_graph = self.is_css_present('div#grade-detail-graph')
        return has_course_info and has_graph

    def scores(self, chapter, section):
        """
        Return a list of (points, max_points) tuples representing the scores
        for the section.

        Example:
            scores('Week 1', 'Lesson 1') --> [(2, 4), (0, 1)]

        Returns `None` if no such chapter and section can be found.
        """

        # Find the index of the section in the chapter
        chapter_index = self._chapter_index(chapter)
        if chapter_index is None:
            return None

        section_index = self._section_index(chapter_index, section)
        if section_index is None:
            return None

        # Retrieve the scores for the section
        return self._section_scores(chapter_index, section_index)

    def _chapter_index(self, title):
        """
        Return the CSS index of the chapter with `title`.
        Returns `None` if it cannot find such a chapter.
        """
        chapter_css = 'ol.chapters li h2'
        chapter_titles = self.css_map(chapter_css, lambda el: el.text.lower().strip())

        try:
            # CSS indices are 1-indexed, so add one to the list index
            return chapter_titles.index(title.lower()) + 1
        except ValueError:
            self.warning("Could not find chapter '{0}'".format(title))
            return None

    def _section_index(self, chapter_index, title):
        """
        Return the CSS index of the section with `title` in the chapter at `chapter_index`.
        Returns `None` if it can't find such a section.
        """

        # This is a hideous CSS selector that means:
        # Get the links containing the section titles in `chapter_index`.
        # The link text is the section title.
        section_css = 'ol.chapters>li:nth-of-type({0}) ol.sections li h3 a'.format(chapter_index)
        section_titles = self.css_map(section_css, lambda el: el.text.lower().strip())

        # The section titles also contain "n of m possible points" on the second line
        # We have to remove this to find the right title
        section_titles = [t.split('\n')[0] for t in section_titles]

        # Some links are blank, so remove them
        section_titles = [t for t in section_titles if t]

        try:
            # CSS indices are 1-indexed, so add one to the list index
            return section_titles.index(title.lower()) + 1
        except ValueError:
            self.warning("Could not find section '{0}'".format(title))
            return None

    def _section_scores(self, chapter_index, section_index):
        """
        Return a list of `(points, max_points)` tuples representing
        the scores in the specified chapter and section.

        `chapter_index` and `section_index` start at 1.
        """
        # This is CSS selector means:
        # Get the scores for the chapter at `chapter_index` and the section at `section_index`
        # Example text of the retrieved elements: "0/1"
        score_css = "ol.chapters>li:nth-of-type({0}) ol.sections>li:nth-of-type({1}) section.scores>ol>li".format(
            chapter_index, section_index
        )

        text_scores = self.css_text(score_css)

        # Convert text scores to tuples of (points, max_points)
        return [tuple(map(int, score.split('/'))) for score in text_scores]
