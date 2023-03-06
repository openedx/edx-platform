(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'common/js/components/utils/view_utils',
        'common/js/spec_helpers/view_helpers'],
    function($, _, Backbone, ViewUtils, ViewHelpers) {
        describe('ViewUtils', function() {
            describe('disabled element while running', function() {
                it("adds 'is-disabled' class to element while action is running and removes it after", function() {
                    var $link,
                        deferred = new $.Deferred(),
                        promise = deferred.promise();
                    setFixtures("<a href='#' id='link'>ripe apples drop about my head</a>");
                    $link = $('#link');
                    expect($link).not.toHaveClass('is-disabled');
                    ViewUtils.disableElementWhileRunning($link, function() { return promise; });
                    expect($link).toHaveClass('is-disabled');
                    deferred.resolve();
                    expect($link).not.toHaveClass('is-disabled');
                });

                it('disables elements within withDisabledElement', function() {
                    var $link,
                        eventCallback,
                        event,
                        deferred = new $.Deferred(),
                        promise = deferred.promise(),
                        MockView = Backbone.View.extend({
                            testFunction: function() {
                                return promise;
                            }
                        }),
                        testView = new MockView();
                    setFixtures("<a href='#' id='link'>ripe apples drop about my head</a>");
                    $link = $('#link');
                    expect($link).not.toHaveClass('is-disabled');
                    eventCallback = ViewUtils.withDisabledElement('testFunction');
                    event = {currentTarget: $link};
                    eventCallback.apply(testView, [event]);
                    expect($link).toHaveClass('is-disabled');
                    deferred.resolve();
                    expect($link).not.toHaveClass('is-disabled');
                });
            });

            describe('progress notification', function() {
                it('shows progress notification and removes it upon success', function() {
                    var testMessage = 'Testing...',
                        deferred = new $.Deferred(),
                        promise = deferred.promise(),
                        notificationSpy = ViewHelpers.createNotificationSpy();
                    ViewUtils.runOperationShowingMessage(testMessage, function() { return promise; });
                    ViewHelpers.verifyNotificationShowing(notificationSpy, /Testing/);
                    deferred.resolve();
                    ViewHelpers.verifyNotificationHidden(notificationSpy);
                });

                it('shows progress notification and leaves it showing upon failure', function() {
                    var testMessage = 'Testing...',
                        deferred = new $.Deferred(),
                        promise = deferred.promise(),
                        notificationSpy = ViewHelpers.createNotificationSpy();
                    ViewUtils.runOperationShowingMessage(testMessage, function() { return promise; });
                    ViewHelpers.verifyNotificationShowing(notificationSpy, /Testing/);
                    deferred.fail();
                    ViewHelpers.verifyNotificationShowing(notificationSpy, /Testing/);
                });
            });

            describe('course/library fields validation', function() {
                describe('without unicode support', function() {
                    it('validates presence of field', function() {
                        var error = ViewUtils.validateURLItemEncoding('', false);
                        expect(error).toBeTruthy();
                    });

                    it('checks for presence of special characters in the field', function() {
                        var error;
                        // Special characters are not allowed.
                        error = ViewUtils.validateURLItemEncoding('my+field', false);
                        expect(error).toBeTruthy();
                        error = ViewUtils.validateURLItemEncoding('2014!', false);
                        expect(error).toBeTruthy();
                        error = ViewUtils.validateURLItemEncoding('*field*', false);
                        expect(error).toBeTruthy();
                        // Spaces not allowed.
                        error = ViewUtils.validateURLItemEncoding('Jan 2014', false);
                        expect(error).toBeTruthy();
                        // -_~. are allowed.
                        error = ViewUtils.validateURLItemEncoding('2015-Math_X1.0~', false);
                        expect(error).toBeFalsy();
                    });

                    it('does not allow unicode characters', function() {
                        var error = ViewUtils.validateURLItemEncoding('Field-\u010d', false);
                        expect(error).toBeTruthy();
                    });
                });

                describe('with unicode support', function() {
                    it('validates presence of field', function() {
                        var error = ViewUtils.validateURLItemEncoding('', true);
                        expect(error).toBeTruthy();
                    });

                    it('checks for presence of spaces', function() {
                        var error = ViewUtils.validateURLItemEncoding('My Field', true);
                        expect(error).toBeTruthy();
                    });

                    it('allows unicode characters', function() {
                        var error = ViewUtils.validateURLItemEncoding('Field-\u010d', true);
                        expect(error).toBeFalsy();
                    });
                });
            });
        });
    });
}).call(this, define || RequireJS.define);
