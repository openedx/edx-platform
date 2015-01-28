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

        $("#add_invoice_button").click(function (e) {

            var invoice_id = $.trim($("#invoice_id").val());
            var amount = $.trim($("#amount").val());
            if (!($.isNumeric(invoice_id))) {
                 $('h3#error-msgs-invoice').html('Please enter invoice id.').show();
                return false
             }
            if (!($.isNumeric(amount))) {
                $('h3#error-msgs-invoice').html('Please enter valid numeric value in amount.').show();
                return false
            }
            $('h3#error-msgs-invoice').hide();
            $("#add_invoice_button").attr('disabled', true);
            $.ajax({
             type: "POST",
             data: {
               "course_id"  :$('#course_id').val(),
               "invoice_id": invoice_id,
               "amount": amount,
               "amount_type": $('input[name="amount_type"]:checked').val(),
               "comments": $("#comments").val()
             },
             url: $('#form_url').val(),
             success: function (data) {
                 location.reload(true);
               },
             error: function(jqXHR, textStatus, errorThrown) {
               var data = $.parseJSON(jqXHR.responseText);
               $('h3#error-msgs-invoice').html(data.message).show();
               $("#add_invoice_button").removeAttr('disabled');
             }
           });

        });
    });
}).call(this, Backbone, $, _);