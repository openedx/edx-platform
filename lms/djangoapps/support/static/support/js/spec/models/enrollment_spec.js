define([
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'support/js/spec_helpers/enrollment_helpers',
    'support/js/models/enrollment'
], function(AjaxHelpers, EnrollmentHelpers, EnrollmentModel) {
    'use strict';

    describe('EnrollmentModel', function() {
        var enrollment;

        beforeEach(function() {
            enrollment = new EnrollmentModel(EnrollmentHelpers.mockEnrollmentData);
            enrollment.url = function() {
                return '/support/enrollment/test-user';
            };
        });

        it('can save an enrollment to the server and updates itself on success', function() {
            var requests = AjaxHelpers.requests(this),
                manual_enrollment = {
                    enrolled_by: 'staff@edx.org',
                    reason: 'Financial Assistance'
                };
            enrollment.updateEnrollment('verified', 'Financial Assistance');
            AjaxHelpers.expectJsonRequest(requests, 'PATCH', '/support/enrollment/test-user', {
                course_id: EnrollmentHelpers.TEST_COURSE,
                new_mode: 'verified',
                old_mode: 'audit',
                reason: 'Financial Assistance'
            });
            AjaxHelpers.respondWithJson(requests, manual_enrollment);
            expect(enrollment.get('mode')).toEqual('verified');
            expect(enrollment.get('manual_enrollment')).toEqual(manual_enrollment);
        });

        it('does not update itself on a server error', function() {
            var requests = AjaxHelpers.requests(this);
            enrollment.updateEnrollment('verified', 'Financial Assistance');
            AjaxHelpers.respondWithError(requests, 500);
            expect(enrollment.get('mode')).toEqual('audit');
            expect(enrollment.get('manual_enrollment')).toEqual({});
        });
    });
});
