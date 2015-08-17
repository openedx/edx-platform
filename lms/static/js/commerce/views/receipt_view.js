/**
 * View for the receipt page.
 */
var edx = edx || {};

(function ($, _, _s, Backbone) {
    'use strict';

    edx.commerce = edx.commerce || {};

    edx.commerce.ReceiptView = Backbone.View.extend({
        useEcommerceApi: true,

        initialize: function () {
            this.useEcommerceApi = !!($.url('?basket_id'));
            _.bindAll(this, 'renderReceipt', 'renderError');

            /* Mix non-conflicting functions from underscore.string (all but include, contains, and reverse) into
             * the Underscore namespace.
             */
            _.mixin(_s.exports());

            this.render();
        },

        renderReceipt: function (data) {
            var templateHtml = $("#receipt-tpl").html(),
                context = {
                    platformName: this.$el.data('platform-name'),
                    verified: this.$el.data('verified').toLowerCase() === 'true'
                };

            // Add the receipt info to the template context
            _.extend(context, {
                receipt: this.receiptContext(data),
                courseKey: this.getOrderCourseKey(data)
            });

            this.$el.html(_.template(templateHtml, context));

            this.trackLinks();
        },

        renderError: function () {
            // Display an error
            $('#error-container').removeClass('hidden');
        },

        render: function () {
            var self = this,
                orderId = $.url('?basket_id') || $.url('?payment-order-num');

            if (orderId && this.$el.data('is-payment-complete')==='True') {
                // Get the order details
                self.$el.removeClass('hidden');
                self.getReceiptData(orderId).then(self.renderReceipt, self.renderError);
            } else {
                self.renderError();
            }
        },

        trackLinks: function () {
            var $verifyNowButton = $('#verify_now_button'),
                $verifyLaterButton = $('#verify_later_button');

            // Track a virtual pageview, for easy funnel reconstruction.
            window.analytics.page('payment', 'receipt');

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
         * Retrieve receipt data from Oscar (via LMS).
         * @param  {int} basketId The basket that was purchased.
         * @return {object}                 JQuery Promise.
         */
        getReceiptData: function (basketId) {
            var urlFormat = this.useEcommerceApi ? '/commerce/baskets/%s/order/' : '/shoppingcart/receipt/%s/';

            return $.ajax({
                url: _.sprintf(urlFormat, basketId),
                type: 'GET',
                dataType: 'json'
            }).retry({times: 5, timeout: 2000, statusCodes: [404]});
        },

        /**
         * Construct the template context from data received
         * from the E-Commerce API.
         *
         * @param  {object} order Receipt data received from the server
         * @return {object}      Receipt template context.
         */
        receiptContext: function (order) {
            var self = this,
                receiptContext;

            if (this.useEcommerceApi) {
                receiptContext = {
                    orderNum: order.number,
                    currency: order.currency,
                    purchasedDatetime: order.date_placed,
                    totalCost: self.formatMoney(order.total_excl_tax),
                    isRefunded: false,
                    items: [],
                    billedTo: null
                };

                if (order.billing_address){
                    receiptContext.billedTo = {
                        firstName: order.billing_address.first_name,
                        lastName: order.billing_address.last_name,
                        city: order.billing_address.city,
                        state: order.billing_address.state,
                        postalCode: order.billing_address.postcode,
                        country: order.billing_address.country
                    }
                }

                receiptContext.items = _.map(
                    order.lines,
                    function (line) {
                        return {
                            lineDescription: line.description,
                            cost: self.formatMoney(line.line_price_excl_tax)
                        };
                    }
                );
            } else {
                receiptContext = {
                    orderNum: order.orderNum,
                    currency: order.currency,
                    purchasedDatetime: order.purchase_datetime,
                    totalCost: self.formatMoney(order.total_cost),
                    isRefunded: order.status === "refunded",
                    billedTo: {
                        firstName: order.billed_to.first_name,
                        lastName: order.billed_to.last_name,
                        city: order.billed_to.city,
                        state: order.billed_to.state,
                        postalCode: order.billed_to.postal_code,
                        country: order.billed_to.country
                    },
                    items: []
                };

                receiptContext.items = _.map(
                    order.items,
                    function (item) {
                        return {
                            lineDescription: item.line_desc,
                            cost: self.formatMoney(item.line_cost)
                        };
                    }
                );
            }

            return receiptContext;
        },

        getOrderCourseKey: function (order) {
            var length, items;
            if (this.useEcommerceApi) {
                length = order.lines.length;
                for (var i = 0; i < length; i++) {
                    var line = order.lines[i],
                        attribute_values = _.filter(line.product.attribute_values, function (attribute) {
                            return attribute.name === 'course_key'
                        });

                    // This method assumes that all items in the order are related to a single course.
                    if (attribute_values.length > 0) {
                        return attribute_values[0]['value'];
                    }
                }
            } else {
                items = _.filter(order.items, function (item) {
                    return item.course_key;
                });

                if (items.length > 0) {
                    return items[0].course_key;
                }
            }

            return null;
        },

        formatMoney: function (moneyStr) {
            return Number(moneyStr).toFixed(2);
        }
    });

    new edx.commerce.ReceiptView({
        el: $('#receipt-container')
    });

})(jQuery, _, _.str, Backbone);
