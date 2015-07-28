/**
 * Use the shopping cart to purchase courses.
 */
;(function (define) {
    'use strict';
    define(['jquery', 'jquery.cookie'], function($) {

        var ShoppingCartInterface = {
            urls: {
                viewCart: "/shoppingcart/",
                addCourse: "/shoppingcart/add/course/"
            },

            headers: {
                'X-CSRFToken': $.cookie('csrftoken')
            },

            /**
             * Add a course to a cart, then redirect to the view cart page.
             * @param {string} courseId The slash-separated course ID to add to the cart.
             */
            addCourseToCart: function( courseId ) {
                $.ajax({
                    url: this.urls.addCourse + courseId + "/",
                    type: 'POST',
                    data: {},
                    headers: this.headers,
                    context: this
                }).always(function() {
                    this.redirect( this.urls.viewCart );
                });
            },

            /**
             * Redirect to a URL.  Mainly useful for mocking out in tests.
             * @param  {string} url The URL to redirect to.
             */
            redirect: function( url ) {
                window.location.href = url;
            }
        };

        return ShoppingCartInterface;
    });
}).call(this, define || RequireJS.define);
