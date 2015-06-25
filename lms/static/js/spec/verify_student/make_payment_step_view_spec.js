define([
        'jquery',
        'underscore',
        'backbone',
        'js/common_helpers/ajax_helpers',
        'js/common_helpers/template_helpers',
        'js/verify_student/views/make_payment_step_view'
    ],
    function( $, _, Backbone, AjaxHelpers, TemplateHelpers, MakePaymentStepView ) {
        'use strict';

        describe( 'edx.verify_student.MakePaymentStepView', function() {

            var PAYMENT_URL = "/pay";

            var PAYMENT_PARAMS = {
                orderId: "test-order",
                signature: "abcd1234"
            };

            var STEP_DATA = {
                minPrice: "12",
                currency: "usd",
                purchaseEndpoint: PAYMENT_URL,
                courseKey: "edx/test/test",
                courseModeSlug: 'verified'
            };

            var SERVER_ERROR_MSG = "An error occurred!";

            var createView = function( stepDataOverrides ) {
                var view = new MakePaymentStepView({
                    el: $( '#current-step-container' ),
                    templateName: 'make_payment_step',
                    stepData: _.extend( _.clone( STEP_DATA ), stepDataOverrides ),
                    errorModel: new ( Backbone.Model.extend({}) )()
                }).render();

                // Stub the payment form submission
                spyOn( view, 'submitForm' ).andCallFake( function() {} );
                return view;
            };

            var expectPriceSelected = function( price ) {
                var sel = $( 'input[name="contribution"]' );

                // check that contribution value is same as price given
                expect( sel.length ).toEqual(1);
                expect( sel.val() ).toEqual(price);
            };

            var expectPaymentButtonEnabled = function( isEnabled ) {
                var appearsDisabled = $( '#pay_button' ).hasClass( 'is-disabled' ),
                    isDisabled = $( '#pay_button' ).prop( 'disabled' );

                expect( !appearsDisabled ).toEqual( isEnabled );
                expect( !isDisabled ).toEqual( isEnabled );
            };

            var expectPaymentDisabledBecauseInactive = function() {
                var payButton = $( '#pay_button' );

                // Payment button should be hidden
                expect( payButton.length ).toEqual(0);
            };

            var goToPayment = function( requests, kwargs ) {
                var params = {
                    contribution: kwargs.amount || "",
                    course_id: kwargs.courseId || ""
                };

                // Click the "go to payment" button
                $( '#pay_button' ).click();

                // Verify that the request was made to the server
                AjaxHelpers.expectRequest(
                    requests, "POST", "/verify_student/create_order/",
                    $.param( params )
                );

                // Simulate the server response
                if ( kwargs.succeeds ) {
                    AjaxHelpers.respondWithJson( requests, PAYMENT_PARAMS );
                } else {
                    AjaxHelpers.respondWithTextError( requests, 400, SERVER_ERROR_MSG );
                }
            };

            var expectPaymentSubmitted = function( view, params ) {
                var form;

                expect(view.submitForm).toHaveBeenCalled();
                form = view.submitForm.mostRecentCall.args[0];

                expect(form.serialize()).toEqual($.param(params));
                expect(form.attr('method')).toEqual("POST");
                expect(form.attr('action')).toEqual(PAYMENT_URL);
            };

            beforeEach(function() {
                window.analytics = jasmine.createSpyObj('analytics', ['track', 'page', 'trackLink']);

                setFixtures( '<div id="current-step-container"></div>' );
                TemplateHelpers.installTemplate( 'templates/verify_student/make_payment_step' );
            });

            it( 'shows users only minimum price', function() {
                var view = createView({}),
                    requests = AjaxHelpers.requests(this);

                expectPriceSelected( STEP_DATA.minPrice );
                expectPaymentButtonEnabled( true );
                goToPayment( requests, {
                    amount: STEP_DATA.minPrice,
                    courseId: STEP_DATA.courseKey,
                    succeeds: true
                });
                expectPaymentSubmitted( view, PAYMENT_PARAMS );
            });

            it( 'by default minimum price is selected if no suggested prices are given', function() {
                var view = createView(),
                    requests = AjaxHelpers.requests( this );

                expectPriceSelected( STEP_DATA.minPrice);
                expectPaymentButtonEnabled( true );

                goToPayment( requests, {
                    amount: STEP_DATA.minPrice,
                    courseId: STEP_DATA.courseKey,
                    succeeds: true
                });
                expectPaymentSubmitted( view, PAYMENT_PARAMS );
            });

            it( 'min price is always selected even if contribution amount is provided', function() {
                // Pre-select a price NOT in the suggestions
                createView({
                    contributionAmount: '99.99'
                });

                // Expect that the price is filled in
                expectPriceSelected( STEP_DATA.minPrice );
            });

            it( 'disables payment for inactive users', function() {
                createView({ isActive: false });
                expectPaymentDisabledBecauseInactive();
            });

            it( 'displays an error if the order could not be created', function() {
                var requests = AjaxHelpers.requests( this ),
                    view = createView({});

                goToPayment( requests, {
                    amount: STEP_DATA.minPrice,
                    courseId: STEP_DATA.courseKey,
                    succeeds: false
                });

                // Expect that an error is displayed
                expect( view.errorModel.get('shown') ).toBe( true );
                expect( view.errorModel.get('errorTitle') ).toEqual( 'Could not submit order' );
                expect( view.errorModel.get('errorMsg') ).toEqual( SERVER_ERROR_MSG );

                // Expect that the payment button is re-enabled
                expectPaymentButtonEnabled( true );
            });

        });
    }
);
