// Jasmine Test Suite: Course modes creation

define([
    'underscore',
    'jquery',
    'js/models/course',
    'js/certificates/views/add_course_mode',
    'common/js/spec_helpers/template_helpers',
    'common/js/spec_helpers/view_helpers',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'
],
function(_, $, Course, AddCourseMode, TemplateHelpers, ViewHelpers, AjaxHelpers) {
    'use strict';

    var SELECTORS = {
        addCourseMode: '.add-course-mode'
    };

    describe('Add Course Modes Spec:', function() {
        beforeEach(function() {
            window.course = new Course({
                id: '5',
                name: 'Course Name',
                url_name: 'course_name',
                org: 'course_org',
                num: 'course_num',
                revision: 'course_rev'
            });
            window.CMS.User = {isGlobalStaff: true, isCourseInstructor: true};

            TemplateHelpers.installTemplate('course-modes', true);
            appendSetFixtures('<div class="wrapper-certificates nav-actions"></div>');
            appendSetFixtures('<p class="account-username">test</p>');
            this.view = new AddCourseMode({
                el: $('.wrapper-certificates'),
                courseId: window.course.id,
                courseModeCreationUrl: '/api/course_modes/v1/courses/' + window.course.id + '/',
                enableCourseModeCreation: true
            });
            appendSetFixtures(this.view.render().el);
        });

        afterEach(function() {
            delete window.course;
            delete window.CMS.User;
        });

        describe('Add course modes', function() {
            it('course mode creation event works fine', function() {
                spyOn(this.view, 'addCourseMode');
                this.view.delegateEvents();
                this.view.$(SELECTORS.addCourseMode).click();
                expect(this.view.addCourseMode).toHaveBeenCalled();
            });

            it('add course modes button works fine', function() {
                var requests = AjaxHelpers.requests(this),
                    notificationSpy = ViewHelpers.createNotificationSpy();
                this.view.$(SELECTORS.addCourseMode).click();
                AjaxHelpers.expectJsonRequest(
                    requests,
                    'POST', '/api/course_modes/v1/courses/' + window.course.id + '/?username=test',
                    {
                        course_id: window.course.id,
                        mode_slug: 'honor',
                        mode_display_name: 'Honor',
                        currency: 'usd'
                    });
                ViewHelpers.verifyNotificationShowing(notificationSpy, /Enabling honor course mode/);
            });

            it('enable course mode creation should be false when method "remove" called', function() {
                this.view.remove();
                expect(this.view.enableCourseModeCreation).toBe(false);
            });

            it('add course mode should be removed when method "remove" called', function() {
                this.view.remove();
                expect(this.view.el.innerHTML).toBe('');
            });

            it('method "show" should call the render function', function() {
                spyOn(this.view, 'render');
                this.view.show();
                expect(this.view.render).toHaveBeenCalled();
            });
        });
    });
});
