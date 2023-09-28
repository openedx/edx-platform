define(

    ['jquery', 'logger', 'js/course_sharing/course_sharing_events'],
    function($, Logger, CourseSharingEvents) {
        'use strict';

        describe('Course sharing click eventing', function() {
            var courseKey1 = 'course-v1:edX+DemoX+Demo_Course',
                courseKey2 = 'course-v1:uog+cs181+2017_LT';

            beforeEach(function() {
                loadFixtures('js/fixtures/course_sharing/course_listings.html');
                // Register course sharing eventing callbacks for both courses.
                CourseSharingEvents(courseKey1);
                CourseSharingEvents(courseKey2);
                spyOn(Logger, 'log');
            });

            it('sends an event only for a course whose facebook link is clicked', function() {
                $(".action-facebook[data-course-id='" + courseKey1 + "']").click();
                expect(Logger.log).toHaveBeenCalledWith('edx.course.share_clicked', {
                    course_id: courseKey1,
                    social_media_site: 'facebook',
                    location: 'dashboard'
                });
                expect(Logger.log.calls.count()).toEqual(1);

                Logger.log.calls.reset();
                $(".action-facebook[data-course-id='" + courseKey2 + "']").click();
                expect(Logger.log).toHaveBeenCalledWith('edx.course.share_clicked', {
                    course_id: courseKey2,
                    social_media_site: 'facebook',
                    location: 'dashboard'
                });
                expect(Logger.log.calls.count()).toEqual(1);
            });

            it('sends an event only for a course whose twitter link is clicked', function() {
                $(".action-twitter[data-course-id='" + courseKey1 + "']").click();
                expect(Logger.log).toHaveBeenCalledWith('edx.course.share_clicked', {
                    course_id: courseKey1,
                    social_media_site: 'twitter',
                    location: 'dashboard'
                });
                expect(Logger.log.calls.count()).toEqual(1);

                Logger.log.calls.reset();
                $(".action-twitter[data-course-id='" + courseKey2 + "']").click();
                expect(Logger.log).toHaveBeenCalledWith('edx.course.share_clicked', {
                    course_id: courseKey2,
                    social_media_site: 'twitter',
                    location: 'dashboard'
                });
                expect(Logger.log.calls.count()).toEqual(1);
            });
        });
    }
);
