define([
    'underscore',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'support/js/spec_helpers/enrollment_helpers',
    'support/js/models/enrollment',
    'support/js/views/enrollment_modal'
], function (_, AjaxHelpers, EnrollmentHelpers, EnrollmentModel, EnrollmentModal) {
    'use strict';

    describe('EnrollmentModal', function () {

        var modal;

        beforeEach(function () {
            var enrollment = new EnrollmentModel(EnrollmentHelpers.mockEnrollmentData);
            enrollment.url = function () {
                return '/support/enrollment/test-user';
            };
            setFixtures('<div class="enrollment-modal-wrapper is-hidden"></div>');
            modal = new EnrollmentModal({
                el: $('.enrollment-modal-wrapper'),
                enrollment: enrollment,
                modes: ['verified', 'audit'],
                reasons: _.reduce(
                    ['Financial Assistance', 'Stampeding Buffalo', 'Angry Customer'],
                    function (acc, x) { acc[x] = x; return acc; },
                    {}
                )
            }).render();
        });

        it('can render itself', function () {
            expect($('.enrollment-modal h1').text()).toContain(
                'Change enrollment for ' + EnrollmentHelpers.TEST_COURSE
            );
            expect($('.enrollment-change-field p').first().text()).toContain('Current enrollment mode: audit');

            _.each(['verified', 'audit'], function (mode) {
                expect($('.enrollment-new-mode').html()).toContain('<option value="' + mode + '">');
            });

            _.each(['', 'Financial Assistance', 'Stampeding Buffalo', 'Angry Customer'], function (reason) {
                expect($('.enrollment-reason').html()).toContain('<option value="' + reason + '">');
            });
        });

        it('is hidden by default', function () {
            expect($('.enrollment-modal-wrapper')).toHaveClass('is-hidden');
        });

        it('can show and hide itself', function () {
            modal.show();
            expect($('.enrollment-modal-wrapper')).not.toHaveClass('is-hidden');
            modal.hide();
            expect($('.enrollment-modal-wrapper')).toHaveClass('is-hidden');
        });

        it('shows errors on submit if a reason is not given', function () {
            expect($('.enrollment-change-errors').css('display')).toEqual('none');
            $('.enrollment-change-submit').click();
            expect($('.enrollment-change-errors').css('display')).not.toEqual('none');
            expect($('.enrollment-change-errors').text()).toContain('Please specify a reason.');
        });

        it('can does not error if a free-form reason is given', function () {
            AjaxHelpers.requests(this);
            $('.enrollment-reason-other').val('For Fun');
            $('.enrollment-change-submit').click();
            expect($('.enrollment-change-errors').css('display')).toEqual('none');
        });

        it('can submit an enrollment change request and hides itself on success', function () {
            var requests = AjaxHelpers.requests(this);
            $('.enrollment-new-mode').val('verified');
            $('.enrollment-reason').val('Financial Assistance');
            $('.enrollment-change-submit').click();
            AjaxHelpers.expectJsonRequest(requests, 'POST', '/support/enrollment/test-user', {
                course_id: EnrollmentHelpers.TEST_COURSE,
                new_mode: 'verified',
                old_mode: 'audit',
                reason: 'Financial Assistance'
            });
            AjaxHelpers.respondWithJson(requests, {
                'enrolled_by': 'staff@edx.org',
                'reason': 'Financial Assistance'
            });
            expect($('.enrollment-change-errors').css('display')).toEqual('none');
        });

        it('shows a message on a server error', function () {
            var requests = AjaxHelpers.requests(this);
            $('.enrollment-new-mode').val('verified');
            $('.enrollment-reason').val('Financial Assistance');
            $('.enrollment-change-submit').click();
            AjaxHelpers.respondWithError(requests, 500);
            expect($('.enrollment-change-errors').css('display')).not.toEqual('none');
            expect($('.enrollment-change-errors').text()).toContain('Something went wrong');
        });

        it('hides itself on cancel', function () {
            var requests = AjaxHelpers.requests(this);
            modal.show();
            $('.enrollment-change-cancel').click();
            AjaxHelpers.expectNoRequests(requests);
            expect($('.enrollment-change-errors').css('display')).toEqual('none');
        });
    });
});
