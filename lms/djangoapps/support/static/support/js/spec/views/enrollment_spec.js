define([
    'underscore',
    'common/js/spec_helpers/ajax_helpers',
    'support/js/spec_helpers/enrollment_helpers',
    'support/js/views/enrollment'
], function (_, AjaxHelpers, EnrollmentHelpers, EnrollmentView) {
    'use strict';

    var enrollmentView,
        createEnrollmentView = function (options) {
            if (_.isUndefined(options)) {
                options = {};
            }
            return new EnrollmentView(_.extend({}, {
                el: '.enrollment-content',
                user: 'test-user',
                enrollmentsUrl: '/support/enrollment/',
                enrollmentSupportUrl: '/support/enrollment/',
            }, options));
        };

    beforeEach(function () {
        setFixtures('<div class="enrollment-content"></div>');
    });

    describe('EnrollmentView', function () {
        it('can render itself without an initial user', function () {
            enrollmentView = createEnrollmentView({user: ''}).render();
            expect($('.enrollment-search input').val()).toBe('');
            expect($('.enrollment-results').length).toBe(0);
        });

        it('renders itself when an initial user is provided', function () {
            var requests = AjaxHelpers.requests(this);
            enrollmentView = createEnrollmentView().render();
            AjaxHelpers.expectRequest(requests, 'GET', '/support/enrollment/test-user', null);
            AjaxHelpers.respondWithJson(requests, [EnrollmentHelpers.mockEnrollmentData]);
            expect($('.enrollment-search input').val()).toBe('test-user');
            expect($('.enrollment-results').length).toBe(1);
            expect($('.enrollment-results td button').first().data()).toEqual({
                course_id: EnrollmentHelpers.TEST_COURSE,
                modes: 'audit,verified'
            });
        });

        it('re-renders itself when its collection changes', function () {
            var requests = AjaxHelpers.requests(this);
            enrollmentView = createEnrollmentView().render();
            spyOn(enrollmentView, 'render').andCallThrough();
            AjaxHelpers.respondWithJson(requests, [EnrollmentHelpers.mockEnrollmentData]);
            expect(enrollmentView.render).toHaveBeenCalled();
        });

        it('shows a modal dialog to change enrollments', function () {
            var requests = AjaxHelpers.requests(this);
            enrollmentView = createEnrollmentView().render();
            AjaxHelpers.respondWithJson(requests, [EnrollmentHelpers.mockEnrollmentData]);
            enrollmentView.$('.change-enrollment-btn').first().click();
            expect($('.enrollment-modal').length).toBe(1);
        });
    });
});
