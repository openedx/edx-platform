from base_studio_test import ContainerBase
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.studio.utils import verify_ordering


class BadComponentTest(ContainerBase):
    """
    Tests that components with bad content do not break the Unit page.
    """
    __test__ = False

    def get_bad_html_content(self):
        """
        Return the "bad" HTML content that has been problematic for Studio.
        """
        pass

    def populate_course_fixture(self, course_fixture):
        """
        Sets up a course structure with a unit and a HTML component with bad data and a properly constructed problem.
        """

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('html', 'Unit HTML', data=self.get_bad_html_content()),
                        XBlockFixtureDesc('problem', 'Unit Problem', data='<problem></problem>')
                    )
                )
            )
        )

    def test_html_comp_visible(self):
        """
        Tests that bad HTML data within an HTML component doesn't prevent Studio from
        displaying the components on the unit page.
        """
        unit = self.go_to_unit_page()
        verify_ordering(self, unit, [{"": ["Unit HTML", "Unit Problem"]}])


class CopiedFromLmsBadContentTest(BadComponentTest):
    """
    Tests that components with HTML copied from the LMS (LmsRuntime) do not break the Unit page.
    """
    __test__ = True

    def get_bad_html_content(self):
        """
        Return the "bad" HTML content that has been problematic for Studio.
        """
        return """
            <div class="xblock xblock-student_view xmodule_display xmodule_HtmlModule xblock-initialized"
            data-runtime-class="LmsRuntime" data-init="XBlockToXModuleShim" data-block-type="html"
            data-runtime-version="1" data-type="HTMLModule" data-course-id="GeorgetownX/HUMW-421-01"
            data-request-token="thisIsNotARealRequestToken"
            data-usage-id="i4x:;_;_GeorgetownX;_HUMW-421-01;_html;_3010cbbecaa1484da6cf8ba01362346a">
            <p>Copied from LMS HTML component</p></div>
            """


class CopiedFromStudioBadContentTest(BadComponentTest):
    """
    Tests that components with HTML copied from the Studio (containing "ui-sortable" class) do not break the Unit page.
    """
    __test__ = True

    def get_bad_html_content(self):
        """
        Return the "bad" HTML content that has been problematic for Studio.
        """
        return """
            <ol class="components ui-sortable">
            <li class="component" data-locator="i4x://Wellesley_College/100/html/6390f1fd3fe640d49580b8415fe1330b"
            data-course-key="Wellesley_College/100/2014_Summer">
            <div class="xblock xblock-student_view xmodule_display xmodule_HtmlModule xblock-initialized"
            data-runtime-class="PreviewRuntime" data-init="XBlockToXModuleShim" data-runtime-version="1"
            data-request-token="thisIsNotARealRequestToken"
            data-usage-id="i4x://Wellesley_College/100/html/6390f1fd3fe640d49580b8415fe1330b"
            data-type="HTMLModule" data-block-type="html">
            <h2>VOICE COMPARISON </h2>
            <p>You can access the experimental <strong >Voice Comparison</strong> tool at the link below.</p>
            </div>
            </li>
            </ol>
            """


class JSErrorBadContentTest(BadComponentTest):
    """
    Tests that components that throw JS errors do not break the Unit page.
    """
    __test__ = True

    def get_bad_html_content(self):
        """
        Return the "bad" HTML content that has been problematic for Studio.
        """
        return "<script>var doesNotExist = BadGlobal.foo;</script>"
