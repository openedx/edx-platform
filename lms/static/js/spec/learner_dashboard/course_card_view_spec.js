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
            context,

            setupView = function(data, isEnrolled) {
                var programData = $.extend({}, data);

                programData.run_modes[0].is_enrolled = isEnrolled;
                setFixtures('<div class="course-card card"></div>');
                courseCardModel = new CourseCardModel(programData);
                view = new CourseCardView({
                    model: courseCardModel
                });
            },

            validateCourseInfoDisplay = function() {
                // DRY validation for course card in enrolled state
                expect(view.$('.header-img').attr('src')).toEqual(context.run_modes[0].course_image_url);
                expect(view.$('.course-details .course-title-link').text().trim()).toEqual(context.display_name);
                expect(view.$('.course-details .course-title-link').attr('href')).toEqual(
                    context.run_modes[0].marketing_url
                );
                expect(view.$('.course-details .course-text .course-key').html()).toEqual(context.key);
                expect(view.$('.course-details .course-text .run-period').html()).toEqual(
                    context.run_modes[0].start_date + ' - ' + context.run_modes[0].end_date
                );
            };

        beforeEach(function() {
                // Redefine this data prior to each test case so that tests can't
                // break each other by modifying data copied by reference.
            context = {
                course_modes: [],
                display_name: 'Astrophysics: Exploring Exoplanets',
                key: 'ANU-ASTRO1x',
                organization: {
                    display_name: 'Australian National University',
                    key: 'ANUx'
                },
                run_modes: [{
                    certificate_url: '',
                    course_image_url: 'http://test.com/image1',
                    course_key: 'course-v1:ANUx+ANU-ASTRO1x+3T2015',
                    course_started: true,
                    course_url: 'https://courses.example.com/courses/course-v1:edX+DemoX+Demo_Course',
                    end_date: 'Jun 13, 2019',
                    enrollment_open_date: 'Apr 1, 2016',
                    is_course_ended: false,
                    is_enrolled: true,
                    is_enrollment_open: true,
                    marketing_url: 'https://www.example.com/marketing/site',
                    mode_slug: 'verified',
                    run_key: '2T2016',
                    start_date: 'Apr 25, 2016',
                    upgrade_url: ''
                }]
            };

            setupView(context, false);
        });

        afterEach(function() {
            view.remove();
        });

        it('should exist', function() {
            expect(view).toBeDefined();
        });

        it('should render the course card based on the data enrolled', function() {
            view.remove();
            setupView(context, true);
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
            var advertisedStart = 'This is an advertised start';
            context.run_modes[0].advertised_start = advertisedStart;
            setupView(context, false);
            expect(view.$('.course-details .course-text .run-period').html()).toEqual(
                advertisedStart + ' - ' + context.run_modes[0].end_date
            );
        });

        it('should only show certificate status section if a certificate has been earned', function() {
            var certUrl = 'sample-certificate';

            expect(view.$('.certificate-status').length).toEqual(0);
            view.remove();

            context.run_modes[0].certificate_url = certUrl;
            setupView(context, false);
            expect(view.$('.certificate-status').length).toEqual(1);
            expect(view.$('.certificate-status .cta-secondary').attr('href')).toEqual(certUrl);
        });

        it('should only show upgrade message section if an upgrade is required', function() {
            var upgradeUrl = '/path/to/upgrade';

            expect(view.$('.upgrade-message').length).toEqual(0);
            view.remove();

            context.run_modes[0].upgrade_url = upgradeUrl;
            setupView(context, false);
            expect(view.$('.upgrade-message').length).toEqual(1);
            expect(view.$('.upgrade-message .cta-primary').attr('href')).toEqual(upgradeUrl);
        });

        it('should not show both the upgrade message and certificate status sections', function() {
                // Verify that no empty elements are left in the DOM.
            context.run_modes[0].upgrade_url = '';
            context.run_modes[0].certificate_url = '';
            setupView(context, false);
            expect(view.$('.upgrade-message').length).toEqual(0);
            expect(view.$('.certificate-status').length).toEqual(0);
            view.remove();

                // Verify that the upgrade message takes priority.
            context.run_modes[0].upgrade_url = '/path/to/upgrade';
            context.run_modes[0].certificate_url = '/path/to/certificate';
            setupView(context, false);
            expect(view.$('.upgrade-message').length).toEqual(1);
            expect(view.$('.certificate-status').length).toEqual(0);
        });

        it('should show a message if an there is an upcoming course run', function() {
            context.run_modes[0].is_enrollment_open = false;

            setupView(context, false);

            expect(view.$('.header-img').attr('src')).toEqual(context.run_modes[0].course_image_url);
            expect(view.$('.course-details .course-title').text().trim()).toEqual(context.display_name);
            expect(view.$('.course-details .course-text .course-key').html()).toEqual(context.key);
            expect(view.$('.course-details .course-text .run-period').length).toBe(0);
            expect(view.$('.no-action-message').text().trim()).toBe('Coming Soon');
            expect(view.$('.enrollment-open-date').text().trim()).toEqual(
                    context.run_modes[0].enrollment_open_date
                );
        });

        it('should show a message if there are no known upcoming course runs', function() {
            context.run_modes[0].is_enrollment_open = false;
            context.run_modes[0].is_course_ended = true;

            setupView(context, false);

            expect(view.$('.header-img').attr('src')).toEqual(context.run_modes[0].course_image_url);
            expect(view.$('.course-details .course-title').text().trim()).toEqual(context.display_name);
            expect(view.$('.course-details .course-text .course-key').html()).toEqual(context.key);
            expect(view.$('.course-details .course-text .run-period').length).toBe(0);
            expect(view.$('.no-action-message').text().trim()).toBe('Not Currently Available');
            expect(view.$('.enrollment-opens').length).toEqual(0);
        });

        it('should link to the marketing site when a URL is available', function() {
            $.each(['.course-image-link', '.course-title-link'], function(index, selector) {
                expect(view.$(selector).attr('href')).toEqual(context.run_modes[0].marketing_url);
            });
        });

        it('should link to the course home when no marketing URL is available', function() {
            context.run_modes[0].marketing_url = null;
            setupView(context, false);

            $.each(['.course-image-link', '.course-title-link'], function(index, selector) {
                expect(view.$(selector).attr('href')).toEqual(context.run_modes[0].course_url);
            });
        });

        it('should not link to the marketing site or the course home if neither URL is available', function() {
            context.run_modes[0].marketing_url = null;
            context.run_modes[0].course_url = null;
            setupView(context, false);

            $.each(['.course-image-link', '.course-title-link'], function(index, selector) {
                expect(view.$(selector).length).toEqual(0);
            });
        });
    });
}
);
