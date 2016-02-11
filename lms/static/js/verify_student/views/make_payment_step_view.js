/**
 * View for the "make payment" step of the payment/verification flow.
 */
var edx = edx || {};

(function( $, _, gettext, interpolate_text ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.MakePaymentStepView = edx.verify_student.StepView.extend({

        templateName: "make_payment_step",
        btnClass: 'action-primary',

        initialize: function( obj ) {
            _.extend( this, obj );
           if (this.templateContext().isABTesting) {
               this.templateName = 'make_payment_step_ab_testing';
               this.btnClass = 'action-primary-blue';
           }
        },

        terms_and_conditions: null,

        defaultContext: function() {
            return {
                isActive: true,
                suggestedPrices: [],
                minPrice: 0,
                sku: '',
                currency: 'eur',
                upgrade: false,
                verificationDeadline: '',
                courseName: '',
                requirements: {},
                hasVisibleReqs: false,
                platformName: '',
                alreadyVerified: false,
                courseModeSlug: 'audit',
                verificationGoodUntil: '',
                isABTesting: false
            };
        },

        _getProductText: function( modeSlug, isUpgrade ) {
            switch ( modeSlug ) {
                case "professional":
                    return gettext( "Professional Education Verified Certificate" );
                case "no-id-professional":
                    return gettext( "Professional Education" );
                default:
                    if ( isUpgrade ) {
                        return gettext( "Verified Certificate upgrade" );
                    } else {
                        return gettext( "Verified Certificate" );
                    }
            }
        },

        _getPaymentButtonText: function(processorName) {
            if (processorName.toLowerCase().substr(0, 11)=='cybersource') {
                return gettext('Checkout');
            } else if (processorName.toLowerCase()=='paypal') {
                return gettext('Checkout with PayPal');
            } else {
                // This is mainly for testing as no other processors are supported right now.
                // Translators: 'processor' is the name of a third-party payment processing vendor (example: "PayPal")
                return 'Payer';
            }
        },

        _getPaymentButtonHtml: function(processorName) {
            var self = this;
            return _.template(
                '<button class="next <%- btnClass %> payment-button" id="<%- name %>" ><%- text %></button> '
            )({name: processorName, text: self._getPaymentButtonText(processorName), btnClass: this.btnClass});
        },

        postRender: function() {
            var templateContext = this.templateContext(),
                hasVisibleReqs = _.some(
                    templateContext.requirements,
                    function( isVisible ) { return isVisible; }
                ),
                // This a hack to appease /lms/static/js/spec/verify_student/pay_and_verify_view_spec.js,
                // which does not load an actual template context.
                processors = templateContext.processors || [],
                self = this;

            // Track a virtual pageview, for easy funnel reconstruction.
            window.analytics.page( 'payment', this.templateName );

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

            // render the name of the product being paid for
            $( 'div.payment-buttons span.product-name').append(
                self._getProductText( templateContext.courseModeSlug, templateContext.upgrade )
            );

            if (processors.length === 0) {
                // No payment processors are enabled at the moment, so show an error message
                this.errorModel.set({
                    errorTitle: gettext('All payment options are currently unavailable.'),
                    errorMsg: gettext('Try the transaction again in a few minutes.'),
                    shown: true
                })
            }
            else {
                // create a button for each payment processor
                _.each(processors.reverse(), function(processorName) {
                    $( 'div.payment-buttons' ).append( self._getPaymentButtonHtml(processorName) );
                });
            }

            // Handle payment submission
            $( '.payment-button' ).on( 'click', _.bind( this.createOrder, this ) );

            // The former call to checkPaymentEnabled does not disable the
            // payment button because it hadn't been introduced in the DOM,
            // yet. So we need to make another call after
            // _getPaymentButtonHtml.
            this.checkPaymentEnabled();
        },

        checkPaymentEnabled: function() {
            var that = this;
            var callback = function(data) {
                if (data.version) {   // an empty json is returned if no terms to validate
                    that.terms_and_conditions = data;
                }
                if (that.terms_and_conditions) {
                    $('.display-fun-payment-terms-text').html(that.terms_and_conditions.text);
                    that.setPaymentEnabled(false);
                    $('#validate-terms').click(function(){
                        $.post("/payment/terms/accept/",
                            function(data) {
                                $('.display-fun-payment-terms').fadeOut()
                                that.setPaymentEnabled(true);
                            }
                        );
                    });
                } else {
                    $('.display-fun-payment-terms').hide();
                    that.setPaymentEnabled(true);
                }
            }
            this.getTerms(callback);
        },
        getTerms: function(callback) {
            if (!this.terms_and_conditions) {
                $.get("/payment/terms/get/",
                    {'always': true},  // show terms at each certified course enrollment, event if already accepted
                    callback
                );
            }
        },
        setPaymentEnabled: function( isEnabled ) {
            if ( _.isUndefined( isEnabled ) ) {
                isEnabled = true;
            }
            $( '.payment-button' )
                .toggleClass( 'is-disabled', !isEnabled )
                .prop( 'disabled', !isEnabled )
                .attr('aria-disabled', !isEnabled);
        },

        // This function invokes the create_order endpoint.  It will either create an order in
        // the lms' shoppingcart or a basket in Otto, depending on which backend the request course
        // mode is configured to use.  In either case, the checkout process will be triggered,
        // and the expected response will consist of an appropriate payment processor endpoint for
        // redirection, along with parameters to be passed along in the request.
        createOrder: function(event) {
            var paymentAmount = this.getPaymentAmount(),
                postData = {
                    'processor': event.target.id,
                    'contribution': paymentAmount,
                    'course_id': this.stepData.courseKey,
                    'sku': this.templateContext().sku
                };

            // Disable the payment button to prevent multiple submissions
            this.setPaymentEnabled( false );

            $( event.target ).toggleClass( 'is-selected' );

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

        handleCreateOrderResponse: function( paymentData ) {
            // At this point, the basket has been created on the server,
            // and we've received signed payment parameters.
            // We need to dynamically construct a form using
            // these parameters, then submit it to the payment processor.
            // This will send the user to an externally-hosted page
            // where she can proceed with payment.
            var form = $( '#payment-processor-form' );

            $( 'input', form ).remove();

            form.attr( 'action', paymentData.payment_page_url );
            form.attr( 'method', 'POST' );

            var payment_form_data = [];

            for(var key in paymentData.payment_form_data) {
                payment_form_data.push([key, paymentData.payment_form_data[key]])
            }
            // FUN/PAYBOX: we alphabeticaly order POSTed fields to ensure order is always the same when signing
            payment_form_data = payment_form_data.sort(function(a, b){
                if (a[0] < b[0])
                  return -1;
                if (a[0] > b[0])
                  return 1;
                return 0;
            });
            _.each( payment_form_data, function( value ) {
                    $('<input>').attr({
                        type: 'hidden',
                        name: value[0],
                        value: value[1]
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
            this.setPaymentEnabled();

            $( '.payment-button' ).toggleClass( 'is-selected', false );
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

})( jQuery, _, gettext, interpolate_text );
