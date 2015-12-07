define(["backbone"],
    function(Backbone) {
        'use strict';
        var getLocationHash, preventBackboneChangingUrl;

        /**
         * Helper method that returns url hash.
         * @return {String} Returns anchor part of current url.
         */
        getLocationHash = function() {
            return window.location.hash;
        };

        /**
         * Prevent Backbone tests from changing the browser's URL.
         *
         * This function modifies Backbone so that tests can navigate
         * without modifying the browser's URL. It works be adding
         * stub versions of Backbone's hash functions so that updating
         * the hash doesn't change the URL but instead updates a
         * local object. The router's callbacks are still invoked
         * so that to the test it appears that navigation is behaving
         * as expected.
         *
         * Note: it is important that tests don't update the browser's
         * URL because subsequent tests could find themselves in an
         * unexpected navigation state.
         */
        preventBackboneChangingUrl = function() {
            var history = {
                currentFragment: ''
            };

            // Stub out the Backbone router so that the browser doesn't actually navigate
            spyOn(Backbone.history, '_updateHash').andCallFake(function (location, fragment, replace) {
                history.currentFragment = fragment;
            });

            // Stub out getHash so that Backbone thinks that the browser has navigated
            spyOn(Backbone.history, 'getHash').andCallFake(function () {
                return history.currentFragment;
            });
        };

        return {
            'getLocationHash': getLocationHash,
            'preventBackboneChangingUrl': preventBackboneChangingUrl
        };
    });
