(function($, analytics) {
    'use strict';

    $(document).ready(function() {
        var errorContainer = $(".credit-error-msg"),
            creditStatusError = errorContainer.data("credit-error");

        if (creditStatusError == "True"){
            errorContainer.toggleClass("is-hidden");
        }

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
        // This event invokes credit request endpoint. It will initiate
        // a credit request for the credit course for the provided user.
        $(".pending-credit-btn").on("click", function(event){
                var courseKey = $(event.target).data("course-key"),
                username = $(event.target).data("user"),
                provider_id = $(event.target).data("provider"),
                postData = {
                    'course_key': courseKey,
                    'username': username
                };
            $.ajax({
                url: 'api/credit/v1/providers/' + provider_id + '/request/',
                type: 'POST',
                headers: {
                    'X-CSRFToken': $.cookie('csrftoken')
                },
                data: JSON.stringify(postData) ,
                context: this,
                success: function(requestData){
                    var form = $('#credit-pending-form');

                    $('input', form).remove();

                    form.attr( 'action', requestData.url );
                    form.attr( 'method', 'POST' );

                    _.each( requestData.parameters, function( value, key ) {
                        $('<input>').attr({
                            type: 'hidden',
                            name: key,
                            value: value
                        }).appendTo(form);
                    });
                    form.submit();
                },
                error: function(xhr){
                    $(".credit-request-pending-msg").hide("is-hidden");
                    $(".pending-credit-btn").hide();
                    errorContainer.toggleClass("is-hidden");
                }
            });
        });
    });
})(jQuery, window.analytics);
