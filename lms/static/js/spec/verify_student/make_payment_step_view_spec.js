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
                suggestedPrices: ["34.56", "78.90"],
                currency: "usd",
                purchaseEndpoint: PAYMENT_URL,
                courseKey: "edx/test/test"
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

            var expectPriceOptions = function( prices ) {
                var sel;
                _.each( prices, function( price ) {
                    sel = _.sprintf( 'input[name="contribution"][value="%s"]', price );
                    expect( $( sel ).length > 0 ).toBe( true );
                });
            };

            var expectPriceSelected = function( price ) {
                var sel = $( _.sprintf( 'input[name="contribution"][value="%s"]', price ) );

                // If the option is available, it should be selected
                if ( sel.length > 0 ) {
                    expect( sel.prop( 'checked' ) ).toBe( true );
                } else {
                    // Otherwise, the text box amount should be filled in
                    expect( $( '#contribution-other' ).prop( 'checked' ) ).toBe( true );
                    expect( $( '#contribution-other-amt' ).val() ).toEqual( price );
               }
            };

            var choosePriceOption = function( price ) {
                var sel = _.sprintf( 'input[name="contribution"][value="%s"]', price );
                $( sel ).trigger( 'click' );
            };

            var enterPrice = function( price ) {
                $( '#contribution-other' ).trigger( 'click' );
                $( '#contribution-other-amt' ).val( price );
            };

            var expectSinglePriceDisplayed = function( price ) {
                var displayedPrice = $( '.contribution-option .label-value' ).text();
                expect( displayedPrice ).toEqual( price );
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

            var expectErrorDisplayed = function( errorTitle ) {
                var actualTitle = $( '#error h3.title' ).text();
                expect( actualTitle ).toEqual( errorTitle );
            };

            beforeEach(function() {
                window.analytics = jasmine.createSpyObj('analytics', ['track', 'page', 'trackLink']);

                setFixtures( '<div id="current-step-container"></div>' );
                TemplateHelpers.installTemplate( 'templates/verify_student/make_payment_step' );
            });

            it( 'allows users to choose a suggested price', function() {
                var view = createView({}),
                    requests = AjaxHelpers.requests(this);

                expectPriceOptions( STEP_DATA.suggestedPrices );
                expectPaymentButtonEnabled( false );

                choosePriceOption( STEP_DATA.suggestedPrices[1] );
                expectPaymentButtonEnabled( true );

                goToPayment( requests, {
                    amount: STEP_DATA.suggestedPrices[1],
                    courseId: STEP_DATA.courseKey,
                    succeeds: true
                });
                expectPaymentSubmitted( view, PAYMENT_PARAMS );
            });

            it( 'allows users to pay the minimum price if no suggested prices are given', function() {
                var view = createView({ suggestedPrices: [] }),
                    requests = AjaxHelpers.requests( this );

                expectSinglePriceDisplayed( STEP_DATA.minPrice );
                expectPaymentButtonEnabled( true );

                goToPayment( requests, {
                    amount: STEP_DATA.minPrice,
                    courseId: STEP_DATA.courseKey,
                    succeeds: true
                });
                expectPaymentSubmitted( view, PAYMENT_PARAMS );
            });

            it( 'allows the user to enter a contribution amount', function() {
                var view = createView({}),
                    requests = AjaxHelpers.requests( this );

                enterPrice( "67.89" );
                expectPaymentButtonEnabled( true );
                goToPayment( requests, {
                    amount: "67.89",
                    courseId: STEP_DATA.courseKey,
                    succeeds: true
                });
                expectPaymentSubmitted( view, PAYMENT_PARAMS );
            });

            it( 'selects in the contribution amount if provided', function() {
                // Pre-select one of the suggested prices
                createView({
                    contributionAmount: STEP_DATA.suggestedPrices[1]
                });

                // Expect that the price is selected
                expectPriceSelected( STEP_DATA.suggestedPrices[1]);
            });

            it( 'fills in the contribution amount if provided', function() {
                // Pre-select a price NOT in the suggestions
                createView({
                    contributionAmount: '99.99'
                });

                // Expect that the price is filled in
                expectPriceSelected( '99.99' );
            });

            it( 'ignores the contribution pre-selected if no suggested prices are given', function() {
                // No suggested prices, but a contribution is set
                createView({
                    suggestedPrices: [],
                    contributionAmount: '99.99'
                });

                // Expect that the single price is displayed
                expectSinglePriceDisplayed( STEP_DATA.minPrice );
            });

            it( 'disables payment for inactive users', function() {
                createView({ isActive: false });
                expectPaymentDisabledBecauseInactive();
            });

            it( 'displays an error if the order could not be created', function() {
                var requests = AjaxHelpers.requests( this ),
                    view = createView({});

                choosePriceOption( STEP_DATA.suggestedPrices[0] );
                goToPayment( requests, {
                    amount: STEP_DATA.suggestedPrices[0],
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
