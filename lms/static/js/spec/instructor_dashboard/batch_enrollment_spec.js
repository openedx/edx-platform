define([
    'jquery',
    'js/instructor_dashboard/membership'
],
    function($) {
        'use strict';
        describe('BatchEnrollment', function() {
            beforeEach(function(done) {
                loadFixtures('js/fixtures/instructor_dashboard/batchenrollment.html');

                this.membershipSection = $('section#membership');
                window.InstructorDashboard.sections.Membership(this.membershipSection);

                jasmine.waitUntil(function() {
                    return $('section#membership').find('.enrollment-button').is(':visible');
                }).always(done);
            });

            it('sends an enrollment ajax call with provided data and selected course mode', function() {
                var courseMode = 'verified',
                    userForEnrollment = 'test_user',
                    studentIdsInput = this.membershipSection.find('textarea[name="student-ids"]'),
                    courseModeSelector = this.membershipSection.find('select#course-modes-list-selector'),
                    enrollButton = this.membershipSection.find('.enrollment-button[value="Enroll"]');

                spyOn($, 'ajax');
                // add the test user in batch enrollment list
                studentIdsInput.val(userForEnrollment);
                // select the course mode 'verified' from course modes dropdown
                courseModeSelector.val(courseMode);
                // click on the button 'Enroll'
                enrollButton.click();

                // now verify that the last ajax POST request has desired parameters
                expect($.ajax.calls.mostRecent().args[0].type).toEqual('POST');
                expect($.ajax.calls.mostRecent().args[0].data).toEqual({
                    action: 'enroll',
                    identifiers: userForEnrollment,
                    auto_enroll: true,
                    course_mode: courseMode,
                    email_students: true,
                    reason: void 0  // set to 'undefined' by default
                });
                expect($.ajax.calls.mostRecent().args[0].url).toEqual(
                    enrollButton.data('endpoint')
                );
            });
        });
    }
);
