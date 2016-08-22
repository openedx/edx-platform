"""
Annotation Component Page.
"""
from bok_choy.page_object import PageObject
from selenium.webdriver import ActionChains


class AnnotationComponentPage(PageObject):
    """
    View of annotation component page.
    """

    url = None
    active_problem = 0

    def is_browser_on_page(self):
        return self.q(css='.annotatable-title').present

    @property
    def component_name(self):
        """
        Return the current problem name.
        """
        return self.q(css='.annotatable-title').text[0]

    def click_reply_annotation(self, problem):
        """
        Mouse over on annotation selector and click on "Reply to Annotation".
        """
        annotation_span_selector = '.annotatable-span[data-problem-id="{}"]'.format(problem)
        self.mouse_hover(self.browser.find_element_by_css_selector(annotation_span_selector))
        self.wait_for_element_visibility(annotation_span_selector, "Reply to Annotation link is visible")

        annotation_reply_selector = '.annotatable-reply[data-problem-id="{}"]'.format(problem)
        self.q(css=annotation_reply_selector).click()

        self.active_problem = problem

    def active_problem_selector(self, sub_selector):
        """
        Return css selector for current active problem with sub_selector.
        """
        return 'div[data-problem-id="{}"] {}'.format(
            self.q(css='.vert-{}'.format(self.active_problem + 1)).map(
                lambda el: el.get_attribute('data-id')).results[0],
            sub_selector,
        )

    def mouse_hover(self, element):
        """
        Mouse over on given element.
        """
        mouse_hover_action = ActionChains(self.browser).move_to_element(element)
        mouse_hover_action.perform()

    def check_scroll_to_problem(self):
        """
        Return visibility of active problem's input selector.
        """
        annotation_input_selector = self.active_problem_selector('.annotation-input')
        return self.q(css=annotation_input_selector).visible

    def answer_problem(self):
        """
        Submit correct answer for active problem.
        """
        self.q(css=self.active_problem_selector('.comment')).fill('Test Response')

        answer_css = self.active_problem_selector('.tag[data-id="{}"]'.format(self.active_problem))
        # Selenium will first move the element into view then click on it.
        self.q(css=answer_css).click()
        # Wait for the click to take effect, which is after the class is applied.
        self.wait_for(lambda: 'selected' in self.q(css=answer_css).attrs('class')[0], description='answer selected')
        # Click the "Check" button.
        self.q(css=self.active_problem_selector('.submit')).click()
        # This will trigger a POST to problem_submit so wait until the response is returned.
        self.wait_for_ajax()

    def check_feedback(self):
        """
        Return visibility of active problem's feedback.
        """
        self.wait_for_element_visibility(
            self.active_problem_selector('.tag-status.correct'), "Correct is visible"
        )
        return self.q(css=self.active_problem_selector('.tag-status.correct')).visible

    def click_return_to_annotation(self):
        """
        Click on active problem's "Return to Annotation" link.
        """
        self.q(css=self.active_problem_selector('.annotation-return')).click()

    def check_scroll_to_annotation(self):
        """
        Return visibility of active annotation component header.
        """
        annotation_header_selector = '.annotation-header'
        return self.q(css=annotation_header_selector).visible
