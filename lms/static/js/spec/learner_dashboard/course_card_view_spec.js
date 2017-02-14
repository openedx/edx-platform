define([
    'backbone',
    'jquery',
    'js/learner_dashboard/models/course_card_model',
    'js/learner_dashboard/views/course_card_view'
], function(Backbone, $, CourseCardModel, CourseCardView) {
    'use strict';

    describe('Course Card View', function() {
        var view = null,
            courseCardModel,
            course,
            startDate = 'Feb 28, 2017',
            endDate = 'May 30, 2017',

            setupView = function(data, isEnrolled) {
                var programData = $.extend({}, data);

                programData.course_runs[0].is_enrolled = isEnrolled;
                setFixtures('<div class="course-card card"></div>');
                courseCardModel = new CourseCardModel(programData);
                view = new CourseCardView({
                    model: courseCardModel
                });
            },

            validateCourseInfoDisplay = function() {
                // DRY validation for course card in enrolled state
                expect(view.$('.header-img').attr('src')).toEqual(course.course_runs[0].image.src);
                expect(view.$('.course-details .course-title-link').text().trim()).toEqual(course.title);
                expect(view.$('.course-details .course-title-link').attr('href')).toEqual(
                    course.course_runs[0].marketing_url
                );
                expect(view.$('.course-details .course-text .course-key').html()).toEqual(course.key);
                expect(view.$('.course-details .course-text .run-period').html()).toEqual(
                    startDate + ' - ' + endDate
                );
            };

        beforeEach(function() {
            // NOTE: This data is redefined prior to each test case so that tests
            // can't break each other by modifying data copied by reference.
            course = {
                key: 'WageningenX+FFESx',
                uuid: '9f8562eb-f99b-45c7-b437-799fd0c15b6a',
                title: 'Systems thinking and environmental sustainability',
                course_runs: [
                    {
                        key: 'course-v1:WageningenX+FFESx+1T2017',
                        title: 'Food Security and Sustainability: Systems thinking and environmental sustainability',
                        image: {
                            src: 'https://example.com/9f8562eb-f99b-45c7-b437-799fd0c15b6a.jpg'
                        },
                        marketing_url: 'https://www.edx.org/course/food-security-sustainability',
                        start: '2017-02-28T05:00:00Z',
                        end: '2017-05-30T23:00:00Z',
                        enrollment_start: '2017-01-18T00:00:00Z',
                        enrollment_end: null,
                        type: 'verified',
                        certificate_url: '',
                        course_url: 'https://courses.example.com/courses/course-v1:WageningenX+FFESx+1T2017',
                        enrollment_open_date: 'Jan 18, 2016',
                        is_course_ended: false,
                        is_enrolled: true,
                        is_enrollment_open: true,
                        upgrade_url: ''
                    }
                ]
            };

            setupView(course, false);
        });

        afterEach(function() {
            view.remove();
        });

        it('should exist', function() {
            expect(view).toBeDefined();
        });

        it('should render the course card based on the data enrolled', function() {
            view.remove();
            setupView(course, true);
            validateCourseInfoDisplay();
        });

        it('should render the course card based on the data not enrolled', function() {
            validateCourseInfoDisplay();
        });

        it('should update render if the course card is_enrolled updated', function() {
            courseCardModel.set({
                is_enrolled: true
            });
            validateCourseInfoDisplay();
        });

        it('should show the course advertised start date', function() {
            var advertisedStart = 'A long time ago...';
            course.course_runs[0].advertised_start = advertisedStart;
            setupView(course, false);
            expect(view.$('.course-details .course-text .run-period').html()).toEqual(
                advertisedStart + ' - ' + endDate
            );
        });

        it('should only show certificate status section if a certificate has been earned', function() {
            var certUrl = 'sample-certificate';

            expect(view.$('.certificate-status').length).toEqual(0);
            view.remove();

            course.course_runs[0].certificate_url = certUrl;
            setupView(course, false);
            expect(view.$('.certificate-status').length).toEqual(1);
            expect(view.$('.certificate-status .cta-secondary').attr('href')).toEqual(certUrl);
        });

        it('should only show upgrade message section if an upgrade is required', function() {
            var upgradeUrl = '/path/to/upgrade';

            expect(view.$('.upgrade-message').length).toEqual(0);
            view.remove();

            course.course_runs[0].upgrade_url = upgradeUrl;
            setupView(course, false);
            expect(view.$('.upgrade-message').length).toEqual(1);
            expect(view.$('.upgrade-message .cta-primary').attr('href')).toEqual(upgradeUrl);
        });

        it('should not show both the upgrade message and certificate status sections', function() {
            // Verify that no empty elements are left in the DOM.
            course.course_runs[0].upgrade_url = '';
            course.course_runs[0].certificate_url = '';
            setupView(course, false);
            expect(view.$('.upgrade-message').length).toEqual(0);
            expect(view.$('.certificate-status').length).toEqual(0);
            view.remove();

            // Verify that the upgrade message takes priority.
            course.course_runs[0].upgrade_url = '/path/to/upgrade';
            course.course_runs[0].certificate_url = '/path/to/certificate';
            setupView(course, false);
            expect(view.$('.upgrade-message').length).toEqual(1);
            expect(view.$('.certificate-status').length).toEqual(0);
        });

        it('should show a message if an there is an upcoming course run', function() {
            course.course_runs[0].is_enrollment_open = false;

            setupView(course, false);

            expect(view.$('.header-img').attr('src')).toEqual(course.course_runs[0].image.src);
            expect(view.$('.course-details .course-title').text().trim()).toEqual(course.title);
            expect(view.$('.course-details .course-text .course-key').html()).toEqual(course.key);
            expect(view.$('.course-details .course-text .run-period').length).toBe(0);
            expect(view.$('.no-action-message').text().trim()).toBe('Coming Soon');
            expect(view.$('.enrollment-open-date').text().trim()).toEqual(
                course.course_runs[0].enrollment_open_date
            );
        });

        it('should show a message if there are no upcoming course runs', function() {
            course.course_runs[0].is_enrollment_open = false;
            course.course_runs[0].is_course_ended = true;

            setupView(course, false);

            expect(view.$('.header-img').attr('src')).toEqual(course.course_runs[0].image.src);
            expect(view.$('.course-details .course-title').text().trim()).toEqual(course.title);
            expect(view.$('.course-details .course-text .course-key').html()).toEqual(course.key);
            expect(view.$('.course-details .course-text .run-period').length).toBe(0);
            expect(view.$('.no-action-message').text().trim()).toBe('Not Currently Available');
            expect(view.$('.enrollment-opens').length).toEqual(0);
        });

        it('should link to the marketing site when a URL is available', function() {
            $.each(['.course-image-link', '.course-title-link'], function(index, selector) {
                expect(view.$(selector).attr('href')).toEqual(course.course_runs[0].marketing_url);
            });
        });

        it('should link to the course home when no marketing URL is available', function() {
            course.course_runs[0].marketing_url = null;
            setupView(course, false);

            $.each(['.course-image-link', '.course-title-link'], function(index, selector) {
                expect(view.$(selector).attr('href')).toEqual(course.course_runs[0].course_url);
            });
        });

        it('should not link to the marketing site or the course home if neither URL is available', function() {
            course.course_runs[0].marketing_url = null;
            course.course_runs[0].course_url = null;
            setupView(course, false);

            $.each(['.course-image-link', '.course-title-link'], function(index, selector) {
                expect(view.$(selector).length).toEqual(0);
            });
        });
    });
}
);
