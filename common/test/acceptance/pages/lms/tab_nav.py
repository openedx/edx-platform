"""
High-level tab navigation.
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import Promise, EmptyPromise


class TabNavPage(PageObject):
    """
    High-level tab navigation.
    """

    url = None

    def is_browser_on_page(self):
        return self.q(css='ol.course-tabs').present

    def go_to_tab(self, tab_name):
        """
        Navigate to the tab `tab_name`.
        """

        if tab_name not in ['Course', 'Home', 'Discussion', 'Theory', 'Progress']:
            self.warning("'{0}' is not a valid tab name".format(tab_name))

        # The only identifier for individual tabs is the link href
        # so we find the tab with `tab_name` in its text.
        tab_css = self._tab_css(tab_name)

        if tab_css is not None:
            self.q(css=tab_css).first.click()
        else:
            self.warning("No tabs found for '{0}'".format(tab_name))

        self.wait_for_page()
        self._is_on_tab_promise(tab_name).fulfill()

    def mathjax_has_rendered(self):
        """
        Check that MathJax has rendered in tab content
        """
        mathjax_container = self.q(css=".static_tab_wrapper .MathJax_SVG")
        EmptyPromise(
            lambda: mathjax_container.present and mathjax_container.visible,
            "MathJax is not visible"
        ).fulfill()

    def is_on_tab(self, tab_name):
        """
        Return a boolean indicating whether the current tab is `tab_name`.
        Because this is a public method, it checks that we're on the right page
        before accessing the DOM.
        """
        return self._is_on_tab(tab_name)

    def _tab_css(self, tab_name):
        """
        Return the CSS to click for `tab_name`.
        If no tabs exist for that name, return `None`.
        """
        all_tabs = self.tab_names

        try:
            tab_index = all_tabs.index(tab_name)
        except ValueError:
            return None
        else:
            return 'ol.course-tabs li:nth-of-type({0}) a'.format(tab_index + 1)

    @property
    def tab_names(self):
        """
        Return the list of available tab names.  If no tab names
        are available, wait for them to load.  Raises a `BrokenPromiseError`
        if the tab names fail to load.
        """
        def _check_func():
            tab_names = self.q(css='ol.course-tabs li a').text
            return (len(tab_names) > 0, tab_names)

        return Promise(_check_func, "Get all tab names").fulfill()

    def _is_on_tab(self, tab_name):
        """
        Return a boolean indicating whether the current tab is `tab_name`.
        This is a private method, so it does NOT enforce the page check,
        which is what we want when we're polling the DOM in a promise.
        """
        current_tab_list = self.q(css='ol.course-tabs > li > a.active').text

        if len(current_tab_list) == 0:
            self.warning("Could not find current tab")
            return False
        else:
            return current_tab_list[0].strip().split('\n')[0] == tab_name

    def _is_on_tab_promise(self, tab_name):
        """
        Return a `Promise` that the user is on the tab `tab_name`.
        """
        # Use the private version of _is_on_tab to skip the page check
        return EmptyPromise(
            lambda: self._is_on_tab(tab_name),
            "{0} is the current tab".format(tab_name)
        )
