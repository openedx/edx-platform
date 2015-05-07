var edx = edx || {};

(function(Backbone, $, _) {
    'use strict';

    edx.instructor_dashboard = edx.instructor_dashboard || {};
    edx.instructor_dashboard.ecommerce = {};

    edx.instructor_dashboard.ecommerce.ExpiryCouponView = Backbone.View.extend({
        el: 'li#add-coupon-modal-field-expiry',
        events: {
            'click input[type="checkbox"]': 'clicked'
        },
        initialize: function() {
            $('li#add-coupon-modal-field-expiry input[name="expiration_date"]').hide();
            _.bindAll(this, 'clicked');
        },
        clicked: function (event) {
            if (event.currentTarget.checked) {
                this.$el.find('#coupon_expiration_date').show();
                this.$el.find('#coupon_expiration_date').focus();
            }
            else {
                this.$el.find('#coupon_expiration_date').hide();
            }
        }
    });

    $(function() {
        $( "#coupon_expiration_date" ).datepicker({
            minDate: 0
        });
        var view = new edx.instructor_dashboard.ecommerce.ExpiryCouponView();
        var request_response = $('.reports .request-response');
        var request_response_error = $('.reports .request-response-error');
        $('input[name="user-enrollment-report"]').click(function(){
            var url = $(this).data('endpoint');
            //return location.href = url;
            $.ajax({
             dataType: "json",
             url: url,
             success: function (data) {
                request_response.text(data['status']);
                return $(".reports .msg-confirm").css({
                  "display": "block"
                });
               },
             error: function(std_ajax_err) {
                request_response_error.text("${_('Error generating grades. Please try again.')}");
                return $(".reports .msg-error").css({
                  "display": "block"
                });
             }
           });
        });
    });
}).call(this, Backbone, $, _);