define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/view_helpers", "js/index",
        "js/views/utils/view_utils"],
    function ($, create_sinon, view_helpers, IndexUtils, ViewUtils) {
        describe("Course listing page", function () {
            var mockIndexPageHTML = readFixtures('mock/mock-index-page.underscore'), fillInFields;

            var fillInFields = function (org, number, run, name) {
                $('.new-course-org').val(org);
                $('.new-course-number').val(number);
                $('.new-course-run').val(run);
                $('.new-course-name').val(name);
            };

            beforeEach(function () {
                view_helpers.installMockAnalytics();
                appendSetFixtures(mockIndexPageHTML);
                IndexUtils.onReady();
            });

            afterEach(function () {
                view_helpers.removeMockAnalytics();
                delete window.source_course_key;
            });

            it("can dismiss notifications", function () {
                var requests = create_sinon.requests(this);
                var reloadSpy = spyOn(ViewUtils, 'reload');
                $('.dismiss-button').click();
                create_sinon.expectJsonRequest(requests, 'DELETE', 'dummy_dismiss_url');
                create_sinon.respondToDelete(requests);
                expect(reloadSpy).toHaveBeenCalled();
            });

            it("saves new courses", function () {
                var requests = create_sinon.requests(this);
                var redirectSpy = spyOn(ViewUtils, 'redirect');
                $('.new-course-button').click()
                fillInFields('DemoX', 'DM101', '2014', 'Demo course');
                $('.new-course-save').click();
                create_sinon.expectJsonRequest(requests, 'POST', '/course/', {
                    org: 'DemoX',
                    number: 'DM101',
                    run: '2014',
                    display_name: 'Demo course'
                });
                create_sinon.respondWithJson(requests, {
                    url: 'dummy_test_url'
                });
                expect(redirectSpy).toHaveBeenCalledWith('dummy_test_url');
            });

            it("displays an error when saving fails", function () {
                var requests = create_sinon.requests(this);
                $('.new-course-button').click();
                fillInFields('DemoX', 'DM101', '2014', 'Demo course');
                $('.new-course-save').click();
                create_sinon.respondWithJson(requests, {
                    ErrMsg: 'error message'
                });
                expect($('.wrap-error')).toHaveClass('is-shown');
                expect($('#course_creation_error')).toContainText('error message');
                expect($('.new-course-save')).toHaveClass('is-disabled');
            });
        });
    });
