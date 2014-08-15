define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/view_helpers", "js/index"],
    function ($, create_sinon, view_helpers, IndexPage) {
        describe("Course listing page", function () {
            var mockIndexPageHTML = readFixtures('mock/mock-index-page.underscore');

            beforeEach(function () {
                view_helpers.installMockAnalytics();
                appendSetFixtures(mockIndexPageHTML);
                IndexPage.onReady();
            });

            afterEach(function () {
                view_helpers.removeMockAnalytics();
                delete window.source_course_key;
            });


            it("can dismiss notifications", function () {
                var requests = create_sinon.requests(this);
                $('.dismiss-button').click();
                create_sinon.expectJsonRequest(requests, 'DELETE', 'dummy_dismiss_url');
            });
        });
    });