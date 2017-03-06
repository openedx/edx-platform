/**
 * Student dashboard credit messaging.
 */

var edx = edx || {};

(function ($, analytics) {
    'use strict';

    $(document).ready(function () {
        var $errorContainer = $(".credit-error-msg"),
            creditStatusError = $errorContainer.data("credit-error");

        if (creditStatusError === "True") {
            $errorContainer.toggleClass("is-hidden");
        }

        // Fire analytics events when the "purchase credit" button is clicked
        $(".purchase-credit-btn").on("click", function (event) {
            var courseKey = $(event.target).data("course-key");
            analytics.track(
                "edx.bi.credit.clicked_purchase_credit",
                {
                    category: "credit",
                    label: courseKey
                }
            );
        });


        // This event invokes credit request endpoint. It will initiate
        // a credit request for the credit course for the provided user.
        $(".pending-credit-btn").on("click", function (event) {
            var $target = $(event.target),
                courseKey = $target.data("course-key"),
                username = $target.data("user"),
                providerId = $target.data("provider");

            event.preventDefault();

            edx.commerce.credit.createCreditRequest(providerId, courseKey, username).fail(function () {
                $(".credit-action").hide();
                $errorContainer.toggleClass("is-hidden");
            });
        });
    });
})(jQuery, window.analytics);
