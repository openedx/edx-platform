define(['backbone', 'jquery', 'js/instructor_dashboard/ecommerce'],
    function (Backbone, $, ExpiryCouponView) {
        'use strict';
        var expiryCouponView;
        describe("edx.instructor_dashboard.ecommerce.ExpiryCouponView", function() {
            beforeEach(function() {
                setFixtures('<li class="field full-width" id="add-coupon-modal-field-expiry"><input id="expiry-check" type="checkbox"/><label for="expiry-check"></label><input type="text" id="coupon_expiration_date" class="field" name="expiration_date" aria-required="true"/></li>');
                expiryCouponView = new ExpiryCouponView();
            });

            it("is defined", function () {
                expect(expiryCouponView).toBeDefined();
            });

            it("triggers the callback when the checkbox is clicked", function () {
                var target = expiryCouponView.$el.find('input[type="checkbox"]');
                spyOn(expiryCouponView, 'clicked');
                expiryCouponView.delegateEvents();
                target.click();
                expect(expiryCouponView.clicked).toHaveBeenCalled();
            });

            it("shows the input field when the checkbox is checked", function () {
                var target = expiryCouponView.$el.find('input[type="checkbox"]');
                target.attr("checked","checked");
                target.click();
                expect(expiryCouponView.$el.find('#coupon_expiration_date')).toHaveAttr('style','display: inline;');
            });

            it("hides the input field when the checkbox is unchecked", function () {
                var target = expiryCouponView.$el.find('input[type="checkbox"]');
                expect(expiryCouponView.$el.find('#coupon_expiration_date')).toHaveAttr('style','display: none;');

            });
        });
    });
