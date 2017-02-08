define([
    'backbone',
    'jquery',
    'js/learner_dashboard/models/course_card_model',
    'js/learner_dashboard/models/course_enroll_model',
    'js/learner_dashboard/views/course_enroll_view'
], function(Backbone, $, CourseCardModel, CourseEnrollModel, CourseEnrollView) {
    'use strict';

    describe('Course Enroll View', function() {
        var view = null,
            courseCardModel,
            courseEnrollModel,
            urlModel,
            setupView,
            singleRunModeList,
            multiRunModeList,
            context = {
                display_name: 'Edx Demo course',
                key: 'edX+DemoX+Demo_Course',
                organization: {
                    display_name: 'edx.org',
                    key: 'edX'
                }
            },
            urls = {
                dashboard_url: '/dashboard',
                id_verification_url: '/verify_student/start_flow/',
                track_selection_url: '/select_track/course/'
            };

        beforeEach(function() {
                // Redefine this data prior to each test case so that tests can't
                // break each other by modifying data copied by reference.
            singleRunModeList = [{
                start_date: 'Apr 25, 2016',
                end_date: 'Jun 13, 2016',
                course_key: 'course-v1:course-v1:edX+DemoX+Demo_Course',
                course_url: 'http://localhost:8000/courses/course-v1:edX+DemoX+Demo_Course/info',
                course_image_url: 'http://test.com/image1',
                marketing_url: 'http://test.com/image2',
                is_course_ended: false,
                mode_slug: 'audit',
                run_key: '2T2016',
                is_enrolled: false,
                is_enrollment_open: true
            }];

            multiRunModeList = [{
                start_date: 'May 21, 2015',
                end_date: 'Sep 21, 2015',
                course_key: 'course-v1:course-v1:edX+DemoX+Demo_Course',
                course_url: 'http://localhost:8000/courses/course-v1:edX+DemoX+Demo_Course/info',
                course_image_url: 'http://test.com/run_2_image_1',
                marketing_url: 'http://test.com/run_2_image_2',
                mode_slug: 'verified',
                is_course_ended: false,
                run_key: '1T2015',
                is_enrolled: false,
                is_enrollment_open: true
            }, {
                start_date: 'Sep 22, 2015',
                end_date: 'Dec 28, 2015',
                course_key: 'course-v1:course-v1:edX+DemoX+Demo_Course',
                course_url: 'http://localhost:8000/courses/course-v1:edX+DemoX+Demo_Course/info',
                course_image_url: 'http://test.com/run_3_image_1',
                marketing_url: 'http://test.com/run_3_image_2',
                is_course_ended: false,
                mode_slug: 'verified',
                run_key: '2T2015',
                is_enrolled: false,
                is_enrollment_open: true
            }];
        });

        setupView = function(runModes, urls) {
            context.run_modes = runModes;
            setFixtures('<div class="course-actions"></div>');
            courseCardModel = new CourseCardModel(context);
            courseEnrollModel = new CourseEnrollModel({}, {
                courseId: courseCardModel.get('course_key')
            });
            if (urls) {
                urlModel = new Backbone.Model(urls);
            }
            view = new CourseEnrollView({
                $parentEl: $('.course-actions'),
                model: courseCardModel,
                enrollModel: courseEnrollModel,
                urlModel: urlModel
            });
        };

        afterEach(function() {
            view.remove();
            urlModel = null;
            courseCardModel = null;
            courseEnrollModel = null;
        });

        it('should exist', function() {
            setupView(singleRunModeList);
            expect(view).toBeDefined();
        });

        it('should render the course enroll view based on not enrolled data', function() {
            setupView(singleRunModeList);
            expect(view.$('.enrollment-info').html().trim()).toEqual('not enrolled');
            expect(view.$('.enroll-button').text().trim()).toEqual('Enroll Now');
            expect(view.$('.run-select').length).toBe(0);
        });

        it('should render the course enroll view based on enrolled data', function() {
            singleRunModeList[0].is_enrolled = true;

            setupView(singleRunModeList);

            expect(view.$('.enrollment-info').html().trim()).toEqual('enrolled');
            expect(view.$('.view-course-link').attr('href')).toEqual(context.run_modes[0].course_url);
            expect(view.$('.view-course-link').text().trim()).toEqual('View Course');
            expect(view.$('.run-select').length).toBe(0);
        });

        it('should allow the learner to view an archived course', function() {
                // Regression test for ECOM-4974.
            singleRunModeList[0].is_enrolled = true;
            singleRunModeList[0].is_enrollment_open = false;
            singleRunModeList[0].is_course_ended = true;

            setupView(singleRunModeList);

            expect(view.$('.view-course-link').text().trim()).toEqual('View Archived Course');
        });

        it('should not render anything if run modes is empty', function() {
            setupView([]);
            expect(view.$('.enrollment-info').length).toBe(0);
            expect(view.$('.run-select').length).toBe(0);
            expect(view.$('.enroll-button').length).toBe(0);
        });

        it('should render run selection drop down if mulitple run available', function() {
            setupView(multiRunModeList);
            expect(view.$('.run-select').length).toBe(1);
            expect(view.$('.run-select').val()).toEqual('');
            expect(view.$('.run-select option').length).toBe(3);
        });

        it('should switch run context if dropdown selection changed', function() {
            setupView(multiRunModeList);
            spyOn(courseCardModel, 'updateRun').and.callThrough();
            expect(view.$('.run-select').val()).toEqual('');
            view.$('.run-select').val(multiRunModeList[1].run_key);
            view.$('.run-select').trigger('change');
            expect(view.$('.run-select').val()).toEqual(multiRunModeList[1].run_key);
            expect(courseCardModel.updateRun)
                    .toHaveBeenCalledWith(multiRunModeList[1].run_key);
            expect(courseCardModel.get('run_key')).toEqual(multiRunModeList[1].run_key);
        });

        it('should enroll learner when enroll button clicked', function() {
            setupView(singleRunModeList);
            expect(view.$('.enroll-button').length).toBe(1);
            spyOn(courseEnrollModel, 'save');
            view.$('.enroll-button').click();
            expect(courseEnrollModel.save).toHaveBeenCalled();
        });

        it('should enroll learner into the updated run with button click', function() {
            setupView(multiRunModeList);
            spyOn(courseEnrollModel, 'save');
            view.$('.run-select').val(multiRunModeList[1].run_key);
            view.$('.run-select').trigger('change');
            view.$('.enroll-button').click();
            expect(courseEnrollModel.save).toHaveBeenCalled();
        });

        it('should redirect to trackSelectionUrl when enrollment success for audit track', function() {
            singleRunModeList[0].is_enrolled = false;
            singleRunModeList[0].mode_slug = 'audit';
            setupView(singleRunModeList, urls);
            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.trackSelectionUrl).toBeDefined();
            spyOn(view, 'redirect');
            view.enrollSuccess();
            expect(view.redirect).toHaveBeenCalledWith(
                    view.trackSelectionUrl + courseCardModel.get('course_key'));
        });


        it('should redirect when enrollment success for no track', function() {
            singleRunModeList[0].is_enrolled = false;
            singleRunModeList[0].mode_slug = null;
            setupView(singleRunModeList, urls);
            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.trackSelectionUrl).toBeDefined();
            spyOn(view, 'redirect');
            view.enrollSuccess();
            expect(view.redirect).toHaveBeenCalledWith(
                    view.trackSelectionUrl + courseCardModel.get('course_key'));
        });

        it('should not redirect when urls not provided', function() {
            singleRunModeList[0].is_enrolled = false;
            singleRunModeList[0].mode_slug = 'verified';
            setupView(singleRunModeList);
            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.verificationUrl).not.toBeDefined();
            expect(view.dashboardUrl).not.toBeDefined();
            expect(view.trackSelectionUrl).not.toBeDefined();
            spyOn(view, 'redirect');
            view.enrollSuccess();
            expect(view.redirect).not.toHaveBeenCalled();
        });

        it('should redirect to track selection on error', function() {
            setupView(singleRunModeList, urls);
            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.trackSelectionUrl).toBeDefined();
            spyOn(view, 'redirect');
            view.enrollError(courseEnrollModel, {status: 500});
            expect(view.redirect).toHaveBeenCalledWith(
                    view.trackSelectionUrl + courseCardModel.get('course_key'));
        });

        it('should redirect to login on 403 error', function() {
            var response = {
                status: 403,
                responseJSON: {
                    user_message_url: 'test_url/haha'
                }};
            setupView(singleRunModeList, urls);
            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.trackSelectionUrl).toBeDefined();
            spyOn(view, 'redirect');
            view.enrollError(courseEnrollModel, response);
            expect(view.redirect).toHaveBeenCalledWith(
                    response.responseJSON.user_message_url);
        });
    });
}
);
