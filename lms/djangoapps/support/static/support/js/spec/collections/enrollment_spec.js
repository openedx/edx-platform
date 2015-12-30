define([
    'common/js/spec_helpers/ajax_helpers',
    'support/js/spec_helpers/enrollment_helpers',
    'support/js/collections/enrollment',
], function (AjaxHelpers, EnrollmentHelpers, EnrollmentCollection) {
    'use strict';

    describe('EnrollmentCollection', function () {
        var enrollmentCollection;

        beforeEach(function () {
            enrollmentCollection = new EnrollmentCollection([EnrollmentHelpers.mockEnrollmentData], {
                user: 'test-user',
                baseUrl: '/support/enrollment/'
            });
        });

        it('sets its URL based on the user', function () {
            expect(enrollmentCollection.url()).toEqual('/support/enrollment/test-user');
        });
    });
});
