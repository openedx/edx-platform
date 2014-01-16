"""
High-level tab navigation.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, fulfill_after


class TabNavPage(PageObject):
    """
    High-level tab navigation.
    """

    url = None

    def is_browser_on_page(self):
        return self.is_css_present('ol.course-tabs')

    def go_to_tab(self, tab_name):
        """
        Navigate to the tab `tab_name`.
        """
        if tab_name not in ['Courseware', 'Course Info', 'Discussion', 'Wiki', 'Progress']:
            self.warning("'{0}' is not a valid tab name".format(tab_name))

        # The only identifier for individual tabs is the link href
        # so we find the tab with `tab_name` in its text.
        tab_css = self._tab_css(tab_name)

        with fulfill_after(self._is_on_tab_promise(tab_name)):
            if tab_css is not None:
                self.css_click(tab_css)
            else:
                self.warning("No tabs found for '{0}'".format(tab_name))

    def is_on_tab(self, tab_name):
        """
        Return a boolean indicating whether the current tab is `tab_name`.
        """
        current_tab_list = self.css_text('ol.course-tabs>li>a.active')

        if len(current_tab_list) == 0:
            self.warning("Could not find current tab")
            return False

        else:
            return (current_tab_list[0].strip().split('\n')[0] == tab_name)

    def _tab_css(self, tab_name):
        """
        Return the CSS to click for `tab_name`.
        """
        all_tabs = self.css_text('ol.course-tabs li a')

        try:
            tab_index = all_tabs.index(tab_name)
        except ValueError:
            return None
        else:
            return 'ol.course-tabs li:nth-of-type({0}) a'.format(tab_index + 1)

    def _is_on_tab_promise(self, tab_name):
        """
        Return a `Promise` that the user is on the tab `tab_name`.
        """
        return EmptyPromise(
            lambda: self.is_on_tab(tab_name),
            "{0} is the current tab".format(tab_name)
        )
