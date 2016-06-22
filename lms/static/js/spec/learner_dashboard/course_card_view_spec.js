define([
        'backbone',
        'jquery',
        'js/learner_dashboard/models/course_card_model',
        'js/learner_dashboard/views/course_card_view'
    ], function (Backbone, $, CourseCardModel, CourseCardView) {
        
        'use strict';
        
        describe('Course Card View', function () {
            var view = null,
                courseCardModel,
                context = {      
                    course_modes: [],
                    display_name: 'Astrophysics: Exploring Exoplanets',
                    key: 'ANU-ASTRO1x',
                    organization: {
                        display_name: 'Australian National University',
                        key: 'ANUx'
                    },
                    run_modes: [{
                        start_date: 'Apr 25, 2016',
                        end_date: 'Jun 13, 2016',
                        course_key: 'course-v1:ANUx+ANU-ASTRO1x+3T2015',
                        course_url: 'http://localhost:8000/courses/course-v1:edX+DemoX+Demo_Course/info',
                        marketing_url: 'https://www.edx.org/course/astrophysics-exploring',
                        course_image_url: 'http://test.com/image1',
                        mode_slug: 'verified',
                        run_key: '2T2016',
                        course_started: true,
                        is_enrolled: true,
                        certificate_url: '',
                    }]
                },

            setupView = function(isEnrolled){
                context.run_modes[0].is_enrolled = isEnrolled;
                setFixtures('<div class="course-card card"></div>');
                courseCardModel = new CourseCardModel(context);
                view = new CourseCardView({
                    model: courseCardModel
                });
            },

            validateCourseInfoDisplay = function(){
                //DRY validation for course card in enrolled state
                expect(view.$('.header-img').attr('src')).toEqual(context.run_modes[0].course_image_url);
                expect(view.$('.course-details .course-title-link').text().trim()).toEqual(context.display_name);
                expect(view.$('.course-details .course-title-link').attr('href')).toEqual(
                    context.run_modes[0].course_url);
                expect(view.$('.course-details .course-text .course-key').html()).toEqual(context.key);
                expect(view.$('.course-details .course-text .run-period').html())
                    .toEqual(context.run_modes[0].start_date + ' - ' + context.run_modes[0].end_date);
            };

            beforeEach(function() {
                setupView(false);
            });

            afterEach(function() {
                view.remove();
            });

            it('should exist', function() {
                expect(view).toBeDefined();
            });

            it('should render the course card based on the data enrolled', function() {
                view.remove();
                setupView(true);
                validateCourseInfoDisplay();
            });

            it('should render the course card based on the data not enrolled', function() {
                validateCourseInfoDisplay();
            });

            it('should update render if the course card is_enrolled updated', function(){
                courseCardModel.set({
                    is_enrolled: true
                });
                validateCourseInfoDisplay();
            });
        });
    }
);
