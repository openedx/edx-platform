/**
 * View for the "make payment" step of the payment/verification flow.
 */
var edx = edx || {};

(function( $, _, gettext ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.MakePaymentStepView = edx.verify_student.StepView.extend({

        defaultContext: function() {
            return {
                isActive: true,
                suggestedPrices: [],
                minPrice: 0,
                currency: 'usd',
                upgrade: false,
                verificationDeadline: '',
                courseName: '',
                requirements: {},
                hasVisibleReqs: false,
                platformName: ''
            };
        },

        postRender: function() {
            var templateContext = this.templateContext(),
                hasVisibleReqs = _.some(
                    templateContext.requirements,
                    function( isVisible ) { return isVisible; }
                );

            // Track a virtual pageview, for easy funnel reconstruction.
            window.analytics.page( 'payment', this.templateName );

            // Set the payment button to disabled by default
            this.setPaymentEnabled( false );

            // Update the contribution amount with the amount the user
            // selected in a previous screen.
            if ( templateContext.contributionAmount ) {
                this.selectPaymentAmount( templateContext.contributionAmount );
            }

            // The contribution section is hidden by default
            // Display it if the user hasn't already selected an amount
            // or is upgrading.
            // In the short-term, we're also displaying this if there
            // are no requirements (e.g. the user already verified).
            // Otherwise, there's absolutely nothing to do on this page.
            // In the future, we'll likely skip directly to payment
            // from the track selection page if this happens.
            if ( templateContext.upgrade || !templateContext.contributionAmount || !hasVisibleReqs ) {
                $( '.wrapper-task' ).removeClass( 'hidden' ).removeAttr( 'aria-hidden' );
            }

            if ( templateContext.suggestedPrices.length > 0 ) {
                // Enable the payment button once an amount is chosen
                $( 'input[name="contribution"]' ).on( 'click', _.bind( this.setPaymentEnabled, this ) );
            } else {
                // If there is only one payment option, then the user isn't shown
                // radio buttons, so we need to enable the radio button.
                this.setPaymentEnabled( true );
            }

            // Handle payment submission
            $( '#pay_button' ).on( 'click', _.bind( this.createOrder, this ) );
        },

        setPaymentEnabled: function( isEnabled ) {
            if ( _.isUndefined( isEnabled ) ) {
                isEnabled = true;
            }
            $( '#pay_button' )
                .toggleClass( 'is-disabled', !isEnabled )
                .prop( 'disabled', !isEnabled )
                .attr('aria-disabled', !isEnabled);
        },

        createOrder: function() {
            var paymentAmount = this.getPaymentAmount(),
                postData = {
                    'contribution': paymentAmount,
                    'course_id': this.stepData.courseKey,
                };

            // Disable the payment button to prevent multiple submissions
            this.setPaymentEnabled( false );

            // Create the order for the amount
            $.ajax({
                url: '/verify_student/create_order/',
                type: 'POST',
                headers: {
                    'X-CSRFToken': $.cookie('csrftoken')
                },
                data: postData,
                context: this,
                success: this.handleCreateOrderResponse,
                error: this.handleCreateOrderError
            });

        },

        handleCreateOrderResponse: function( paymentParams ) {
            // At this point, the order has been created on the server,
            // and we've received signed payment parameters.
            // We need to dynamically construct a form using
            // these parameters, then submit it to the payment processor.
            // This will send the user to a hosted order page,
            // where she can enter credit card information.
            var form = $( '#payment-processor-form' );

            $( 'input', form ).remove();

            form.attr( 'action', this.stepData.purchaseEndpoint );
            form.attr( 'method', 'POST' );

            _.each( paymentParams, function( value, key ) {
                $('<input>').attr({
                    type: 'hidden',
                    name: key,
                    value: value
                }).appendTo(form);
            });

            // Marketing needs a way to tell the difference between users
            // leaving for the payment processor and users dropping off on
            // this page. A virtual pageview can be used to do this.
            window.analytics.page( 'payment', 'payment_processor_step' );

            this.submitForm( form );
        },

        handleCreateOrderError: function( xhr ) {
            var errorMsg = gettext( 'An error has occurred. Please try again.' );

            if ( xhr.status === 400 ) {
                errorMsg = xhr.responseText;
            }

            this.errorModel.set({
                errorTitle: gettext( 'Could not submit order' ),
                errorMsg: errorMsg,
                shown: true
            });

            // Re-enable the button so the user can re-try
            this.setPaymentEnabled( true );
        },

        getPaymentAmount: function() {
            var contributionInput = $( 'input[name="contribution"]:checked' , this.el),
                amount = null;

            if ( contributionInput.attr('id') === 'contribution-other' ) {
                amount = $( 'input[name="contribution-other-amt"]' , this.el ).val();
            } else {
                amount = contributionInput.val();
            }

            // If no suggested prices are available, then the user does not
            // get the option to select a price.  Default to the minimum.
            if ( !amount ) {
                amount = this.templateContext().minPrice;
            }

            return amount;
        },

        selectPaymentAmount: function( amount ) {
            var amountFloat = parseFloat( amount ),
                foundPrice,
                sel;

            // Check if we have a suggested price that matches the amount
            foundPrice = _.find(
                this.stepData.suggestedPrices,
                function( price ) {
                    return parseFloat( price ) === amountFloat;
                }
            );

            // If we've found an option for the price, select it.
            if ( foundPrice ) {
                sel = _.sprintf( 'input[name="contribution"][value="%s"]', foundPrice );
                $( sel ).prop( 'checked', true );
            } else {
                // Otherwise, enter the value into the text box
                $( '#contribution-other-amt', this.el ).val( amount );
                $( '#contribution-other', this.el ).prop( 'checked', true );
            }

            // In either case, enable the payment button
            this.setPaymentEnabled();

            return amount;
        },

        // Stubbed out in tests
        submitForm: function( form ) {
            form.submit();
        }

    });

})( jQuery, _, gettext );
