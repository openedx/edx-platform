define([
    'backbone',
    'jquery',
    'js/learner_dashboard/views/entitlement_unenrollment_view'
], function(Backbone, $, EntitlementUnenrollmentView) {
    'use strict';

    describe('EntitlementUnenrollmentView', function() {
        var view = null,
            options = {
                dashboardPath: '/dashboard',
                signInPath: '/login'
            },

            initView = function() {
                return new EntitlementUnenrollmentView(options);
            },

            modalHtml = '<a id="link1" class="js-entitlement-action-unenroll"                         ' +
                        '   data-course-name="Test Course 1"                                          ' +
                        '   data-course-number="test1"                                                ' +
                        '   data-entitlement-api-endpoint="/test/api/endpoint/1">Unenroll</a>         ' +
                        '<a id="link2" class="js-entitlement-action-unenroll"                         ' +
                        '   data-course-name="Test Course 2"                                          ' +
                        '   data-course-number="test2"                                                ' +
                        '   data-entitlement-api-endpoint="/test/api/endpoint/2">Unenroll</a>         ' +
                        '<div class="js-entitlement-unenrollment-modal">                              ' +
                        '  <span class="js-entitlement-unenrollment-modal-header-text"></span>        ' +
                        '  <span class="js-entitlement-unenrollment-modal-error-text"></span>         ' +
                        '  <button class="js-entitlement-unenrollment-modal-submit">Unenroll</button> ' +
                        '</div>                                                                       ';

        beforeEach(function() {
            setFixtures(modalHtml);
            view = initView();
        });

        afterEach(function() {
            view.remove();
        });

        describe('when an unenroll link is clicked', function() {
            it('should reset the modal and set the correct values for header/submit', function() {
                var $link1 = $('#link1'),
                    $link2 = $('#link2'),
                    $headerTxt = $('.js-entitlement-unenrollment-modal-header-text'),
                    $errorTxt = $('.js-entitlement-unenrollment-modal-error-text'),
                    $submitBtn = $('.js-entitlement-unenrollment-modal-submit');

                $link1.trigger('click');
                expect($headerTxt.html().startsWith('Are you sure you want to unenroll from Test Course 1')).toBe(true);
                expect($submitBtn.data()).toEqual({entitlementApiEndpoint: '/test/api/endpoint/1'});
                expect($submitBtn.prop('disabled')).toBe(false);
                expect($errorTxt.html()).toEqual('');
                expect($errorTxt.hasClass('entitlement-unenrollment-modal-error-text-visible')).toBe(false);

                // Set an error so that we can see that the modal is reset properly when clicked again
                view.setError('This is an error');
                expect($errorTxt.html()).toEqual('This is an error');
                expect($errorTxt.hasClass('entitlement-unenrollment-modal-error-text-visible')).toBe(true);
                expect($submitBtn.prop('disabled')).toBe(true);

                $link2.trigger('click');
                expect($headerTxt.html().startsWith('Are you sure you want to unenroll from Test Course 2')).toBe(true);
                expect($submitBtn.data()).toEqual({entitlementApiEndpoint: '/test/api/endpoint/2'});
                expect($submitBtn.prop('disabled')).toBe(false);
                expect($errorTxt.html()).toEqual('');
                expect($errorTxt.hasClass('entitlement-unenrollment-modal-error-text-visible')).toBe(false);
            });
        });

        describe('when the unenroll submit button is clicked', function() {
            it('should send a DELETE request to the configured apiEndpoint', function() {
                var $submitBtn = $('.js-entitlement-unenrollment-modal-submit'),
                    apiEndpoint = '/test/api/endpoint/1';

                view.setSubmitData(apiEndpoint);

                spyOn($, 'ajax').and.callFake(function(opts) {
                    expect(opts.url).toEqual(apiEndpoint);
                    expect(opts.method).toEqual('DELETE');
                    expect(opts.complete).toBeTruthy();
                });

                $submitBtn.trigger('click');
                expect($.ajax).toHaveBeenCalled();
            });

            it('should set an error and disable submit if the apiEndpoint has not been properly set', function() {
                var $errorTxt = $('.js-entitlement-unenrollment-modal-error-text'),
                    $submitBtn = $('.js-entitlement-unenrollment-modal-submit');

                expect($submitBtn.data()).toEqual({});
                expect($submitBtn.prop('disabled')).toBe(false);
                expect($errorTxt.html()).toEqual('');
                expect($errorTxt.hasClass('entitlement-unenrollment-modal-error-text-visible')).toBe(false);

                spyOn($, 'ajax');
                $submitBtn.trigger('click');
                expect($.ajax).not.toHaveBeenCalled();

                expect($submitBtn.data()).toEqual({});
                expect($submitBtn.prop('disabled')).toBe(true);
                expect($errorTxt.html()).toEqual(view.genericErrorMsg);
                expect($errorTxt.hasClass('entitlement-unenrollment-modal-error-text-visible')).toBe(true);
            });

            describe('when the unenroll request is complete', function() {
                it('should redirect to the dashboard if the request was successful', function() {
                    var $submitBtn = $('.js-entitlement-unenrollment-modal-submit'),
                        apiEndpoint = '/test/api/endpoint/1';

                    view.setSubmitData(apiEndpoint);

                    spyOn($, 'ajax').and.callFake(function(opts) {
                        expect(opts.url).toEqual(apiEndpoint);
                        expect(opts.method).toEqual('DELETE');
                        expect(opts.complete).toBeTruthy();

                        opts.complete({
                            status: 204,
                            responseJSON: {detail: 'success'}
                        });
                    });
                    spyOn(view, 'redirectTo');

                    $submitBtn.trigger('click');
                    expect($.ajax).toHaveBeenCalled();
                    expect(view.redirectTo).toHaveBeenCalledWith(view.dashboardPath);
                });

                it('should redirect to the login page if the request failed with an auth error', function() {
                    var $submitBtn = $('.js-entitlement-unenrollment-modal-submit'),
                        apiEndpoint = '/test/api/endpoint/1';

                    view.setSubmitData(apiEndpoint);

                    spyOn($, 'ajax').and.callFake(function(opts) {
                        expect(opts.url).toEqual(apiEndpoint);
                        expect(opts.method).toEqual('DELETE');
                        expect(opts.complete).toBeTruthy();

                        opts.complete({
                            status: 401,
                            responseJSON: {detail: 'Authentication credentials were not provided.'}
                        });
                    });
                    spyOn(view, 'redirectTo');

                    $submitBtn.trigger('click');
                    expect($.ajax).toHaveBeenCalled();
                    expect(view.redirectTo).toHaveBeenCalledWith(
                        view.signInPath + '?next=' + encodeURIComponent(view.dashboardPath)
                    );
                });

                it('should set an error and disable submit if a non-auth error occurs', function() {
                    var $errorTxt = $('.js-entitlement-unenrollment-modal-error-text'),
                        $submitBtn = $('.js-entitlement-unenrollment-modal-submit'),
                        apiEndpoint = '/test/api/endpoint/1';

                    view.setSubmitData(apiEndpoint);

                    spyOn($, 'ajax').and.callFake(function(opts) {
                        expect(opts.url).toEqual(apiEndpoint);
                        expect(opts.method).toEqual('DELETE');
                        expect(opts.complete).toBeTruthy();

                        opts.complete({
                            status: 400,
                            responseJSON: {detail: 'Bad request.'}
                        });
                    });
                    spyOn(view, 'redirectTo');

                    expect($submitBtn.prop('disabled')).toBe(false);
                    expect($errorTxt.html()).toEqual('');
                    expect($errorTxt.hasClass('entitlement-unenrollment-modal-error-text-visible')).toBe(false);

                    $submitBtn.trigger('click');

                    expect($submitBtn.prop('disabled')).toBe(true);
                    expect($errorTxt.html()).toEqual(view.genericErrorMsg);
                    expect($errorTxt.hasClass('entitlement-unenrollment-modal-error-text-visible')).toBe(true);

                    expect($.ajax).toHaveBeenCalled();
                    expect(view.redirectTo).not.toHaveBeenCalled();
                });
            });
        });
    });
}
);
