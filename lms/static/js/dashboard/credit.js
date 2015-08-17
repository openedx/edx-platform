(function($, analytics) {
    'use strict';

    $(document).ready(function() {
        // Fire analytics events when the "purchase credit" button is clicked
        $(".purchase-credit-btn").on("click", function(event) {
            var courseKey = $(event.target).data("course-key");
            analytics.track(
                "edx.bi.credit.clicked_purchase_credit",
                {
                    category: "credit",
                    label: courseKey
                }
            );
        });
    });
})(jQuery, window.analytics);
