define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/view_helpers", "js/views/course_rerun"],
    function ($, create_sinon, view_helpers, CourseRerunUtils) {
        describe("Create course rerun page", function () {
            var selectors = {
                    courseOrg: '.rerun-course-org',
                    courseNumber: '.rerun-course-number',
                    courseRun: '.rerun-course-run',
                    courseName: '.rerun-course-name',
                    errorField: '.tip-error',
                    saveButton: '.rerun-course-save',
                    cancelButton: '.rerun-course-cancel',
                    errorMessage: '.wrapper-error'
                },
                classes = {
                    hidden: 'is-hidden',
                    error: 'error',
                    disabled: 'is-disabled',
                    processing: 'is-processing'
                },
                mockCreateCourseRerunHTML = readFixtures('mock/mock-create-course-rerun.underscore');

            var fillInFields = function (org, number, run, name) {
                $(selectors.courseOrg).val(org);
                $(selectors.courseNumber).val(number);
                $(selectors.courseRun).val(run);
                $(selectors.courseName).val(name);
            };

            beforeEach(function () {
                view_helpers.installMockAnalytics();
                window.source_course_key = 'test_course_key';
                appendSetFixtures(mockCreateCourseRerunHTML);
                CourseRerunUtils.onReady();
            });

            afterEach(function () {
                view_helpers.removeMockAnalytics();
                delete window.source_course_key;
            });

            describe("Field validation", function () {
                it("returns a message for an empty string", function () {
                    var message = CourseRerunUtils.validateRequiredField('');
                    expect(message).not.toBe('');
                });

                it("does not return a message for a non empty string", function () {
                    var message = CourseRerunUtils.validateRequiredField('edX');
                    expect(message).toBe('');
                });
            });

            describe("Error messages", function () {
                var setErrorMessage = function(selector, message) {
                    var element = $(selector).parent();
                    CourseRerunUtils.setNewCourseFieldInErr(element, message);
                    return element;
                };

                it("shows an error message", function () {
                    var element = setErrorMessage(selectors.courseOrg, 'error message');
                    expect(element).toHaveClass(classes.error);
                    expect(element.children(selectors.errorField)).not.toHaveClass(classes.hidden);
                    expect(element.children(selectors.errorField)).toContainText('error message');
                });

                it("hides an error message", function () {
                    var element = setErrorMessage(selectors.courseOrg, '');
                    expect(element).not.toHaveClass(classes.error);
                    expect(element.children(selectors.errorField)).toHaveClass(classes.hidden);
                });

                it("disables the save button", function () {
                    setErrorMessage(selectors.courseOrg, 'error message');
                    expect($(selectors.saveButton)).toHaveClass(classes.disabled);
                });

                it("enables the save button when all errors are removed", function () {
                    setErrorMessage(selectors.courseOrg, 'error message 1');
                    setErrorMessage(selectors.courseNumber, 'error message 2');
                    expect($(selectors.saveButton)).toHaveClass(classes.disabled);
                    setErrorMessage(selectors.courseOrg, '');
                    setErrorMessage(selectors.courseNumber, '');
                    expect($(selectors.saveButton)).not.toHaveClass(classes.disabled);
                });

                it("does not enable the save button when errors remain", function () {
                    setErrorMessage(selectors.courseOrg, 'error message 1');
                    setErrorMessage(selectors.courseNumber, 'error message 2');
                    expect($(selectors.saveButton)).toHaveClass(classes.disabled);
                    setErrorMessage(selectors.courseOrg, '');
                    expect($(selectors.saveButton)).toHaveClass(classes.disabled);
                });
            });

            it("saves course reruns", function () {
                var requests = create_sinon.requests(this);
                window.source_course_key = 'test_course_key';
                fillInFields('DemoX', 'DM101', '2014', 'Demo course');
                $(selectors.saveButton).click();
                create_sinon.expectJsonRequest(requests, 'POST', '/course/', {
                    source_course_key: 'test_course_key',
                    org: 'DemoX',
                    number: 'DM101',
                    run: '2014',
                    display_name: 'Demo course'
                });
                expect($(selectors.saveButton)).toHaveClass(classes.disabled);
                expect($(selectors.saveButton)).toHaveClass(classes.processing);
                expect($(selectors.cancelButton)).toHaveClass(classes.hidden);
            });

            it("displays an error when saving fails", function () {
                var requests = create_sinon.requests(this);
                fillInFields('DemoX', 'DM101', '2014', 'Demo course');
                $(selectors.saveButton).click();
                create_sinon.respondWithJson(requests, {
                    ErrMsg: 'error message'
                });
                expect($(selectors.errorMessage)).not.toHaveClass(classes.hidden);
                expect($(selectors.errorMessage)).toContainText('error message');
                expect($(selectors.saveButton)).not.toHaveClass(classes.processing);
                expect($(selectors.cancelButton)).not.toHaveClass(classes.hidden);
            });

            it("does not save if there are validation errors", function () {
                var requests = create_sinon.requests(this);
                fillInFields('DemoX', 'DM101', '', 'Demo course');
                $(selectors.saveButton).click();
                expect(requests.length).toBe(0);
            });
        });
    });
