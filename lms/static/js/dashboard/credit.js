/**
 * Student dashboard credit messaging.
 */

/* eslint-disable-next-line no-use-before-define, no-var */
var edx = edx || {};

(function($, analytics) {
    'use strict';

    $(document).ready(function() {
        // eslint-disable-next-line no-var
        var $errorContainer = $('.credit-error-msg'),
            creditStatusError = $errorContainer.data('credit-error');

        if (creditStatusError === 'True') {
            $errorContainer.toggleClass('is-hidden');
        }

        // Fire analytics events when the "purchase credit" button is clicked
        $('.purchase-credit-btn').on('click', function(event) {
            // eslint-disable-next-line no-var
            var courseKey = $(event.target).data('course-key');
            analytics.track(
                'edx.bi.credit.clicked_purchase_credit',
                {
                    category: 'credit',
                    label: courseKey
                }
            );
        });

        // This event invokes credit request endpoint. It will initiate
        // a credit request for the credit course for the provided user.
        $('.pending-credit-btn').on('click', function(event) {
            // eslint-disable-next-line no-var
            var $target = $(event.target),
                courseKey = $target.data('course-key'),
                username = $target.data('user'),
                providerId = $target.data('provider');

            event.preventDefault();

            edx.commerce.credit.createCreditRequest(providerId, courseKey, username).fail(function() {
                $('.credit-action').hide();
                $errorContainer.toggleClass('is-hidden');
            });
        });
    });
// eslint-disable-next-line no-undef
}(jQuery, window.analytics));
