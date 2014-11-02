define(["jquery", "js/common_helpers/ajax_helpers", "js/spec_helpers/view_helpers", "js/index",
        "js/views/utils/view_utils"],
    function ($, AjaxHelpers, ViewHelpers, IndexUtils, ViewUtils) {
        describe("Course listing page", function () {
            var mockIndexPageHTML = readFixtures('mock/mock-index-page.underscore');

            var fillInFields = function (org, number, run, name) {
                $('.new-course-org').val(org);
                $('.new-course-number').val(number);
                $('.new-course-run').val(run);
                $('.new-course-name').val(name);
            };

            var fillInLibraryFields = function(org, number, name) {
                $('.new-library-org').val(org).keyup();
                $('.new-library-number').val(number).keyup();
                $('.new-library-name').val(name).keyup();
            };

            beforeEach(function () {
                ViewHelpers.installMockAnalytics();
                appendSetFixtures(mockIndexPageHTML);
                IndexUtils.onReady();
            });

            afterEach(function () {
                ViewHelpers.removeMockAnalytics();
                delete window.source_course_key;
            });

            it("can dismiss notifications", function () {
                var requests = AjaxHelpers.requests(this);
                var reloadSpy = spyOn(ViewUtils, 'reload');
                $('.dismiss-button').click();
                AjaxHelpers.expectJsonRequest(requests, 'DELETE', 'dummy_dismiss_url');
                AjaxHelpers.respondToDelete(requests);
                expect(reloadSpy).toHaveBeenCalled();
            });

            it("saves new courses", function () {
                var requests = AjaxHelpers.requests(this);
                var redirectSpy = spyOn(ViewUtils, 'redirect');
                $('.new-course-button').click()
                fillInFields('DemoX', 'DM101', '2014', 'Demo course');
                $('.new-course-save').click();
                AjaxHelpers.expectJsonRequest(requests, 'POST', '/course/', {
                    org: 'DemoX',
                    number: 'DM101',
                    run: '2014',
                    display_name: 'Demo course'
                });
                AjaxHelpers.respondWithJson(requests, {
                    url: 'dummy_test_url'
                });
                expect(redirectSpy).toHaveBeenCalledWith('dummy_test_url');
            });

            it("displays an error when saving fails", function () {
                var requests = AjaxHelpers.requests(this);
                $('.new-course-button').click();
                fillInFields('DemoX', 'DM101', '2014', 'Demo course');
                $('.new-course-save').click();
                AjaxHelpers.respondWithJson(requests, {
                    ErrMsg: 'error message'
                });
                expect($('.create-course .wrap-error')).toHaveClass('is-shown');
                expect($('#course_creation_error')).toContainText('error message');
                expect($('.new-course-save')).toHaveClass('is-disabled');
            });

            it("saves new libraries", function () {
                var requests = AjaxHelpers.requests(this);
                var redirectSpy = spyOn(ViewUtils, 'redirect');
                $('.new-library-button').click();
                fillInLibraryFields('DemoX', 'DM101', 'Demo library');
                $('.new-library-save').click();
                AjaxHelpers.expectJsonRequest(requests, 'POST', '/library/', {
                    org: 'DemoX',
                    number: 'DM101',
                    display_name: 'Demo library'
                });
                AjaxHelpers.respondWithJson(requests, {
                    url: 'dummy_test_url'
                });
                expect(redirectSpy).toHaveBeenCalledWith('dummy_test_url');
            });

            it("displays an error when saving a library fails", function () {
                var requests = AjaxHelpers.requests(this);
                $('.new-library-button').click();
                fillInLibraryFields('DemoX', 'DM101', 'Demo library');
                $('.new-library-save').click();
                AjaxHelpers.respondWithJson(requests, {
                    ErrMsg: 'error message'
                });
                expect($('.create-library .wrap-error')).toHaveClass('is-shown');
                expect($('#library_creation_error')).toContainText('error message');
                expect($('.new-library-save')).toHaveClass('is-disabled');
            });
        });
    });
