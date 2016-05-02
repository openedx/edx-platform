define(['common/js/spec_helpers/ajax_helpers', 'js/shoppingcart/shoppingcart'],
    function(AjaxHelpers) {
        'use strict';

        describe("edx.shoppingcart.showcart.CartView", function() {
            var view = null;
            var requests = null;

            beforeEach(function() {
                setFixtures('<section class="wrapper confirm-enrollment shopping-cart cart-view"><form action="" method="post"><input type="hidden" name="" value="" /><i class="icon fa fa-caret-right"></i><input type="submit" value="Payment"/></form></section>');

                view = new edx.shoppingcart.showcart.CartView({
                    el: $('.confirm-enrollment.cart-view form')
                });

                spyOn(view, 'responseFromServer').andCallFake(function() {});

                // Spy on AJAX requests
                requests = AjaxHelpers.requests(this);

                view.submit();

                // Verify that the client contacts the server to
                // check for all th valid cart items
                AjaxHelpers.expectRequest(
                    requests, "GET", "/shoppingcart/verify_cart/"
                );
            });

            it("cart has invalid items, course enrollment has been closed", function() {
                // Simulate a response from the server containing the
                // parameter 'is_course_enrollment_closed'. This decides that
                // do we have all the cart items valid in the cart or not
                AjaxHelpers.respondWithJson(requests, {
                    is_course_enrollment_closed: true
                });

                expect(view.responseFromServer).toHaveBeenCalled();
                var data = view.responseFromServer.mostRecentCall.args[0]
                expect(data.is_course_enrollment_closed).toBe(true);

            });

            it("cart has all valid items, course enrollment is still open", function() {
                // Simulate a response from the server containing the
                // parameter 'is_course_enrollment_closed'. This decides that
                // do we have all the cart items valid in the cart or not
                 AjaxHelpers.respondWithJson(requests, {
                    is_course_enrollment_closed: false
                });

                expect(view.responseFromServer).toHaveBeenCalled();
                var data = view.responseFromServer.mostRecentCall.args[0]
                expect(data.is_course_enrollment_closed).toBe(false);

            });
        });
    }
);
