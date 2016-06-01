define([
        'backbone',
        'jquery',
        'js/learner_dashboard/views/course_card_view'
    ], function (Backbone, $, CourseCardView) {
        
        'use strict';
        
        describe('Course Card View', function () {
            var view = null,
                courseCardModel,
                setupView,
                context = {      
                    certificate_url: '',
                    course_end: 'Jun 13, 2016',
                    course_modes: [],
                    course_key: 'course-v1:ANUx+ANU-ASTRO1x+3T2015',
                    courseware_url: 'http://localhost:8000/courses/course-v1:edX+DemoX+Demo_Course/info',
                    course_start: 'Apr 25, 2016',
                    course_started: true,
                    display_name: 'Astrophysics: Exploring Exoplanets',
                    image_url: 'https://testimage.com/image',
                    key: 'ANU-ASTRO1x',
                    marketing_url: 'https://www.edx.org/course/astrophysics-exploring-exoplanets-anux-anu-astro2x-1',
                    organization: {
                        display_name: 'Australian National University',
                        key: 'ANUx'
                    },
                    run_modes: [{
                        course_key: '12313',
                        mode_slug: 'verified',
                        run_key: '2T2016',
                        start_date: ''
                    }]
                };

            setupView = function(enrollment_status){
                context.enrollment_status = enrollment_status;
                setFixtures('<div class="course-card card"></div>');
                courseCardModel = new Backbone.Model(context);
                view = new CourseCardView({
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

            it('should render the course card based on the data enrolled', function() {
                view.remove();
                setupView('enrolled');
                expect(view.$('.header-img').attr('src')).toEqual(context.image_url);
                expect(view.$('.course-details .course-title').html()).toEqual(context.display_name);
                expect(view.$('.course-details .course-key').html()).toEqual(context.key);
                expect(view.$('.course-details .enrollment-info').html())
                    .toEqual(context.course_start + ' - ' + context.course_end);
                expect(view.$('.course-details .course-link').attr('href')).toEqual(context.courseware_url);
            });

            it('should render the course card based on the data not enrolled', function() {
                expect(view.$('.header-img').attr('src')).toEqual(context.image_url);
                expect(view.$('.course-details .course-title').html()).toEqual(context.display_name);
                expect(view.$('.course-details .course-key').html()).toEqual(context.key);
                expect(view.$('.course-details .enrollment-info').html()).toEqual('Not Yet Enrolled');
                expect(view.$('.course-details .course-link').attr('href')).toEqual(context.marketing_url);
            });
        });
    }
);
