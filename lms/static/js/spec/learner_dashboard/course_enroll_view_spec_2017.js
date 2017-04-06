define([
    'backbone',
    'jquery',
    'js/learner_dashboard/models/course_card_model',
    'js/learner_dashboard/models/course_enroll_model',
    'js/learner_dashboard/views/course_enroll_view_2017'
], function(Backbone, $, CourseCardModel, CourseEnrollModel, CourseEnrollView) {
    'use strict';

    describe('Course Enroll View', function() {
        var view = null,
            courseCardModel,
            courseEnrollModel,
            urlModel,
            setupView,
            singleCourseRunList,
            multiCourseRunList,
            course = {
                key: 'WageningenX+FFESx',
                uuid: '9f8562eb-f99b-45c7-b437-799fd0c15b6a',
                title: 'Systems thinking and environmental sustainability',
                owners: [
                    {
                        uuid: '0c6e5fa2-96e8-40b2-9ebe-c8b0df2a3b22',
                        key: 'WageningenX',
                        name: 'Wageningen University & Research'
                    }
                ]
            },
            urls = {
                commerce_api_url: '/commerce',
                track_selection_url: '/select_track/course/'
            };

        beforeEach(function() {
            // Stub analytics tracking
            window.analytics = jasmine.createSpyObj('analytics', ['track']);

            // NOTE: This data is redefined prior to each test case so that tests
            // can't break each other by modifying data copied by reference.
            singleCourseRunList = [{
                key: 'course-v1:WageningenX+FFESx+1T2017',
                uuid: '2f2edf03-79e6-4e39-aef0-65436a6ee344',
                title: 'Food Security and Sustainability: Systems thinking and environmental sustainability',
                image: {
                    src: 'https://example.com/2f2edf03-79e6-4e39-aef0-65436a6ee344.jpg'
                },
                marketing_url: 'https://www.edx.org/course/food-security-sustainability-systems-wageningenx-ffesx',
                start: '2017-02-28T05:00:00Z',
                end: '2017-05-30T23:00:00Z',
                enrollment_start: '2017-01-18T00:00:00Z',
                enrollment_end: null,
                type: 'verified',
                certificate_url: '',
                course_url: 'https://courses.example.com/courses/course-v1:edX+DemoX+Demo_Course',
                enrollment_open_date: 'Jan 18, 2016',
                is_course_ended: false,
                is_enrolled: false,
                is_enrollment_open: true,
                upgrade_url: ''
            }];

            multiCourseRunList = [{
                key: 'course-v1:WageningenX+FFESx+2T2016',
                uuid: '9bbb7844-4848-44ab-8e20-0be6604886e9',
                title: 'Food Security and Sustainability: Systems thinking and environmental sustainability',
                image: {
                    src: 'https://example.com/9bbb7844-4848-44ab-8e20-0be6604886e9.jpg'
                },
                short_description: 'Learn how to apply systems thinking to improve food production systems.',
                marketing_url: 'https://www.edx.org/course/food-security-sustainability-systems-wageningenx-stesx',
                start: '2016-09-08T04:00:00Z',
                end: '2016-11-11T00:00:00Z',
                enrollment_start: null,
                enrollment_end: null,
                pacing_type: 'instructor_paced',
                type: 'verified',
                certificate_url: '',
                course_url: 'https://courses.example.com/courses/course-v1:WageningenX+FFESx+2T2016',
                enrollment_open_date: 'Jan 18, 2016',
                is_course_ended: false,
                is_enrolled: false,
                is_enrollment_open: true
            }, {
                key: 'course-v1:WageningenX+FFESx+1T2017',
                uuid: '2f2edf03-79e6-4e39-aef0-65436a6ee344',
                title: 'Food Security and Sustainability: Systems thinking and environmental sustainability',
                image: {
                    src: 'https://example.com/2f2edf03-79e6-4e39-aef0-65436a6ee344.jpg'
                },
                marketing_url: 'https://www.edx.org/course/food-security-sustainability-systems-wageningenx-ffesx',
                start: '2017-02-28T05:00:00Z',
                end: '2017-05-30T23:00:00Z',
                enrollment_start: '2017-01-18T00:00:00Z',
                enrollment_end: null,
                type: 'verified',
                certificate_url: '',
                course_url: 'https://courses.example.com/courses/course-v1:WageningenX+FFESx+1T2017',
                enrollment_open_date: 'Jan 18, 2016',
                is_course_ended: false,
                is_enrolled: false,
                is_enrollment_open: true
            }];
        });

        setupView = function(courseRuns, urlMap) {
            course.course_runs = courseRuns;
            setFixtures('<div class="course-actions"></div>');
            courseCardModel = new CourseCardModel(course);
            courseEnrollModel = new CourseEnrollModel({}, {
                courseId: courseCardModel.get('course_run_key')
            });
            if (urlMap) {
                urlModel = new Backbone.Model(urlMap);
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
            setupView(singleCourseRunList);
            expect(view).toBeDefined();
        });

        it('should render the course enroll view when not enrolled', function() {
            setupView(singleCourseRunList);
            expect(view.$('.enroll-button').text().trim()).toEqual('Enroll Now');
            expect(view.$('.run-select').length).toBe(0);
        });

        it('should render the course enroll view when enrolled', function() {
            singleCourseRunList[0].is_enrolled = true;

            setupView(singleCourseRunList);
            expect(view.$el.html().trim()).toEqual('');
            expect(view.$('.run-select').length).toBe(0);
        });

        it('should not render anything if course runs are empty', function() {
            setupView([]);

            expect(view.$('.enrollment-info').length).toBe(0);
            expect(view.$('.run-select').length).toBe(0);
            expect(view.$('.enroll-button').length).toBe(0);
        });

        it('should render run selection dropdown if multiple course runs are available', function() {
            setupView(multiCourseRunList);

            expect(view.$('.run-select').length).toBe(1);
            expect(view.$('.run-select').val()).toEqual(multiCourseRunList[0].key);
            expect(view.$('.run-select option').length).toBe(2);
        });

        it('should enroll learner when enroll button is clicked with one course run available', function() {
            setupView(singleCourseRunList);

            expect(view.$('.enroll-button').length).toBe(1);

            spyOn(courseEnrollModel, 'save');

            view.$('.enroll-button').click();

            expect(courseEnrollModel.save).toHaveBeenCalled();
        });

        it('should enroll learner when enroll button is clicked with multiple course runs available', function() {
            setupView(multiCourseRunList);

            spyOn(courseEnrollModel, 'save');

            view.$('.run-select').val(multiCourseRunList[1].key);
            view.$('.run-select').trigger('change');
            view.$('.enroll-button').click();

            expect(courseEnrollModel.save).toHaveBeenCalled();
        });

        it('should redirect to track selection when audit enrollment succeeds', function() {
            singleCourseRunList[0].is_enrolled = false;
            singleCourseRunList[0].mode_slug = 'audit';

            setupView(singleCourseRunList, urls);

            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.trackSelectionUrl).toBeDefined();

            spyOn(view, 'redirect');

            view.enrollSuccess();

            expect(view.redirect).toHaveBeenCalledWith(
                view.trackSelectionUrl + courseCardModel.get('course_run_key'));
        });

        it('should redirect to track selection when enrollment in an unspecified mode is attempted', function() {
            singleCourseRunList[0].is_enrolled = false;
            singleCourseRunList[0].mode_slug = null;

            setupView(singleCourseRunList, urls);

            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.trackSelectionUrl).toBeDefined();

            spyOn(view, 'redirect');

            view.enrollSuccess();

            expect(view.redirect).toHaveBeenCalledWith(
                view.trackSelectionUrl + courseCardModel.get('course_run_key')
            );
        });

        it('should not redirect when urls are not provided', function() {
            singleCourseRunList[0].is_enrolled = false;
            singleCourseRunList[0].mode_slug = 'verified';

            setupView(singleCourseRunList);

            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.verificationUrl).not.toBeDefined();
            expect(view.dashboardUrl).not.toBeDefined();
            expect(view.trackSelectionUrl).not.toBeDefined();

            spyOn(view, 'redirect');

            view.enrollSuccess();

            expect(view.redirect).not.toHaveBeenCalled();
        });

        it('should redirect to track selection on error', function() {
            setupView(singleCourseRunList, urls);

            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.trackSelectionUrl).toBeDefined();

            spyOn(view, 'redirect');

            view.enrollError(courseEnrollModel, {status: 500});
            expect(view.redirect).toHaveBeenCalledWith(
                view.trackSelectionUrl + courseCardModel.get('course_run_key')
            );
        });

        it('should redirect to login on 403 error', function() {
            var response = {
                status: 403,
                responseJSON: {
                    user_message_url: 'redirect/to/this'
                }
            };

            setupView(singleCourseRunList, urls);

            expect(view.$('.enroll-button').length).toBe(1);
            expect(view.trackSelectionUrl).toBeDefined();

            spyOn(view, 'redirect');

            view.enrollError(courseEnrollModel, response);

            expect(view.redirect).toHaveBeenCalledWith(
                response.responseJSON.user_message_url
            );
        });

        it('sends analytics event when enrollment succeeds', function() {
            setupView(singleCourseRunList, urls);
            spyOn(view, 'redirect');
            view.enrollSuccess();
            expect(window.analytics.track).toHaveBeenCalledWith(
                'edx.bi.user.program-details.enrollment'
            );
        });
    });
}
);
