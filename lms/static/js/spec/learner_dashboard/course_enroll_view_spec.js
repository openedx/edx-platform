define([
        'backbone',
        'jquery',
        'js/learner_dashboard/models/course_card_model',
        'js/learner_dashboard/views/course_enroll_view'
    ], function (Backbone, $, CourseCardModel, CourseEnrollView) {
        
        'use strict';
        
        describe('Course Enroll View', function () {
            var view = null,
                courseCardModel,
                setupView,
                context = {      
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
                        course_image_url: 'http://test.com/image1',
                        marketing_url: 'http://test.com/image2',
                        mode_slug: 'verified',
                        run_key: '2T2016',
                        is_enrolled: 'enrolled',
                        certificate_url: '',
                    }]
                };

            setupView = function(){
                setFixtures('<div class="enrollment-container"></div>');
                courseCardModel = new CourseCardModel(context);
                view = new CourseEnrollView({
                    model: courseCardModel
                });
            };

            beforeEach(function() {
                setupView(null);
            });

            afterEach(function() {
                view.remove();
            });

            it('should exist', function() {
                expect(view).toBeDefined();
            });

            it('should render the course enroll view based on the data', function() {
                expect(view.$('.enrollment-info').html().trim()).toEqual('not enrolled');
                expect(view.$('.enroll-button').text().trim()).toEqual('Enroll Now');
            });
        });
    }
);
