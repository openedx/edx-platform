/**
 * View for the "payment confirmation" step of the payment/verification flow.
 */
var edx = edx || {};

(function($, _, gettext) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.PaymentConfirmationStepView = edx.verify_student.StepView.extend({

        templateName: 'payment_confirmation_step',

        defaultContext: function() {
            return {
                courseKey: '',
                courseName: '',
                coursewareUrl: '',
                platformName: '',
                requirements: []
            };
        },

        /**
         * Retrieve receipt information from the shopping cart.
         *
         * We make this request from JavaScript to encapsulate
         * the verification Django app from the shopping cart app.
         *
         * This method checks the query string param
         * ?payment-order-num, which can be set by the shopping cart
         * before redirecting to the payment confirmation page.
         * This step then reads the param and requests receipt information
         * from the shopping cart.  At no point does the "verify student"
         * Django app interact directly with the shopping cart.
         *
         * @param  {object} templateContext The original template context.
         * @return {object} A JQuery promise that resolves with the modified
         *                    template context.
         */
        updateContext: function(templateContext) {
            var view = this;
            return $.Deferred(
                function(defer) {
                    var paymentOrderNum = $.url('?payment-order-num');
                    if (paymentOrderNum) {
                        // If there is a payment order number, try to retrieve
                        // the receipt information from the shopping cart.
                        view.getReceiptData(paymentOrderNum).done(
                            function(data) {
                                // Add the receipt info to the template context
                                _.extend(templateContext, {receipt: this.receiptContext(data)});
                                defer.resolveWith(view, [templateContext]);
                            }
                        ).fail(function() {
                            // Display an error
                            // This can occur if the user does not have access to the receipt
                            // or the order number is invalid.
                            defer.rejectWith(
                                this,
                                [
                                    gettext('Error'),
                                    gettext('Could not retrieve payment information')
                                ]
                            );
                        });
                    } else {
                        // If no payment order is provided, return the original context
                        // The template is responsible for displaying a default state.
                        _.extend(templateContext, {receipt: null});
                        defer.resolveWith(view, [templateContext]);
                    }
                }
            ).promise();
        },

        /**
         * The "Verify Later" button goes directly to the dashboard,
         * The "Verify Now" button sends the user to the verification flow.
         * For this reason, we don't need any custom click handlers here, except for
         * those used to track business intelligence events.
         */
        postRender: function() {
            var $verifyNowButton = $('#verify_now_button'),
                $verifyLaterButton = $('#verify_later_button');

            // Track a virtual pageview, for easy funnel reconstruction.
            window.analytics.page('payment', this.templateName);

            // Track the user's decision to verify immediately
            window.analytics.trackLink($verifyNowButton, 'edx.bi.user.verification.immediate', {
                category: 'verification'
            });

            // Track the user's decision to defer their verification
            window.analytics.trackLink($verifyLaterButton, 'edx.bi.user.verification.deferred', {
                category: 'verification'
            });
        },

        /**
         * Retrieve receipt data from the shoppingcart.
         * @param  {int} paymentOrderNum The order number of the payment.
         * @return {object}                 JQuery Promise.
         */
        getReceiptData: function(paymentOrderNum) {
            return $.ajax({
                url: _.sprintf('/shoppingcart/receipt/%s/', paymentOrderNum),
                type: 'GET',
                dataType: 'json',
                context: this
            });
        },

        /**
         * Construct the template context from data received
         * from the shopping cart receipt.
         *
         * @param  {object} data Receipt data received from the server
         * @return {object}      Receipt template context.
         */
        receiptContext: function(data) {
            var view = this,
                receiptContext;

            receiptContext = {
                orderNum: data.orderNum,
                currency: data.currency,
                purchasedDatetime: data.purchase_datetime,
                totalCost: view.formatMoney(data.total_cost),
                isRefunded: data.status === 'refunded',
                billedTo: {
                    firstName: data.billed_to.first_name,
                    lastName: data.billed_to.last_name,
                    city: data.billed_to.city,
                    state: data.billed_to.state,
                    postalCode: data.billed_to.postal_code,
                    country: data.billed_to.country
                },
                items: []
            };

            receiptContext.items = _.map(
                data.items,
                function(item) {
                    return {
                        lineDescription: item.line_desc,
                        cost: view.formatMoney(item.line_cost)
                    };
                }
            );

            return receiptContext;
        },

        formatMoney: function(moneyStr) {
            return Number(moneyStr).toFixed(2);
        }
    });
})(jQuery, _, gettext);
