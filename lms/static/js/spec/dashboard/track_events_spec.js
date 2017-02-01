(function(define) {
    'use strict';
    define([
        'jquery',
        'js/dashboard/track_events'
    ],
    function($) {
        describe('edx.dashboard.trackEvents', function() {
            beforeEach(function() {
                // Stub the analytics event tracker
                window.analytics = jasmine.createSpyObj('analytics', ['track', 'page', 'trackLink']);
                loadFixtures('js/fixtures/dashboard/dashboard.html');
            });

            it('sends an analytics event when the user clicks course title link', function() {
                var $courseTitle = $('.course-title > a');
                window.edx.dashboard.trackCourseTitleClicked(
                    $courseTitle,
                    window.edx.dashboard.generateTrackProperties);
                // Verify that analytics events fire when the 'course title link' is clicked.
                expect(window.analytics.trackLink).toHaveBeenCalledWith(
                    $courseTitle,
                    'edx.bi.dashboard.course_title.clicked',
                     window.edx.dashboard.generateTrackProperties
                );
            });

            it('sends an analytics event when the user clicks course image link', function() {
                var $courseImage = $('.cover');
                window.edx.dashboard.trackCourseImageLinkClicked(
                    $courseImage,
                    window.edx.dashboard.generateTrackProperties);
                // Verify that analytics events fire when the 'course image link' is clicked.
                expect(window.analytics.trackLink).toHaveBeenCalledWith(
                    $courseImage,
                    'edx.bi.dashboard.course_image.clicked',
                    window.edx.dashboard.generateTrackProperties
                );
            });


            it('sends an analytics event when the user clicks enter course link', function() {
                var $enterCourse = $('.enter-course');
                window.edx.dashboard.trackEnterCourseLinkClicked(
                    $enterCourse,
                    window.edx.dashboard.generateTrackProperties);
                // Verify that analytics events fire when the 'enter course link' is clicked.
                expect(window.analytics.trackLink).toHaveBeenCalledWith(
                    $enterCourse,
                    'edx.bi.dashboard.enter_course.clicked',
                    window.edx.dashboard.generateTrackProperties
                );
            });

            it('sends an analytics event when the user clicks enter course link', function() {
                var $dropDown = $('.wrapper-action-more');
                window.edx.dashboard.trackCourseOptionDropdownClicked(
                    $dropDown,
                    window.edx.dashboard.generateTrackProperties);
                // Verify that analytics events fire when the options dropdown is engaged.
                expect(window.analytics.trackLink).toHaveBeenCalledWith(
                    $dropDown,
                    'edx.bi.dashboard.course_options_dropdown.clicked',
                    window.edx.dashboard.generateTrackProperties
                );
            });

            it('sends an analytics event when the user clicks the learned about verified track link', function() {
                var $learnVerified = $('.verified-info');
                window.edx.dashboard.trackLearnVerifiedLinkClicked(
                    $learnVerified,
                    window.edx.dashboard.generateTrackProperties);
                // Verify that analytics events fire when the 'Learned about verified track' link is clicked.
                expect(window.analytics.trackLink).toHaveBeenCalledWith(
                    $learnVerified,
                    'edx.bi.dashboard.verified_info_link.clicked',
                    window.edx.dashboard.generateTrackProperties
                );
            });

            it('sends an analytics event when the user clicks find courses button', function() {
                var $findCourse = $('.btn-find-courses'),
                    property = {
                        category: 'dashboard',
                        label: null
                    };
                window.edx.dashboard.trackFindCourseBtnClicked($findCourse, property);
                // Verify that analytics events fire when the 'user clicks find the course' button.
                expect(window.analytics.trackLink).toHaveBeenCalledWith(
                    $findCourse,
                    'edx.bi.dashboard.find_courses_button.clicked',
                    property
                );
            });
        });
    });
}).call(this, window.define);
