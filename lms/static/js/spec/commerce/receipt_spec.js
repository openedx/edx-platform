define([
        'js/commerce/views/receipt_view'
    ],
    function (){
        'use strict';
        describe("edx.commerce.ReceiptView", function(ReceiptView) {
            var view, data = null;

            beforeEach(function(){
                loadFixtures("js/fixtures/commerce/checkout_receipt.html");

                var receiptFixture = readFixtures("templates/commerce/receipt.underscore");
                appendSetFixtures(
                    "<script id=\"receipt-tpl\" type=\"text/template\" >" + receiptFixture + "</script>"
                );
                data = {
                    "status": "Open",
                    "billed_to": {
                        "city": "dummy city",
                        "first_name": "john",
                        "last_name": "doe",
                        "country": "AL",
                        "line2": "line2",
                        "line1": "line1",
                        "state": "",
                        "postcode": "12345"
                    },
                    "lines": [
                        {
                            "status": "Open",
                            "unit_price_excl_tax": "10.00",
                            "product": {
                                "attribute_values": [
                                    {
                                        "name": "certificate_type",
                                        "value": "verified"
                                    },
                                    {
                                        "name": "course_key",
                                        "value": "course-v1:edx+dummy+2015_T3"
                                    }
                                ],
                                "stockrecords": [
                                    {
                                        "price_currency": "USD",
                                        "product": 123,
                                        "partner_sku": "1234ABC",
                                        "partner": 1,
                                        "price_excl_tax": "10.00",
                                        "id": 123
                                    }
                                ],
                                "product_class": "Seat",
                                "title": "Dummy title",
                                "url": "https://ecom.edx.org/api/v2/products/123/",
                                "price": "10.00",
                                "expires": null,
                                "is_available_to_buy": true,
                                "id": 123,
                                "structure": "child"
                            },
                            "line_price_excl_tax": "10.00",
                            "description": "dummy description",
                            "title": "dummy title",
                            "quantity": 1
                        }
                    ],
                    "number": "EDX-123456",
                    "date_placed": "2016-01-01T01:01:01Z",
                    "currency": "USD",
                    "total_excl_tax": "10.00"
                };
                view = new ReceiptView({el: $('#receipt-container')});
                view.renderReceipt(data);
            });
            it("sends analytic event when receipt is rendered", function() {
                expect(window.analytics.track).toHaveBeenCalledWith(
                    "Completed Order",
                    {
                        orderId: "EDX-123456",
                        total: "10.00",
                        currency: "USD"
                    }
                );

            });

        });
    }
);
