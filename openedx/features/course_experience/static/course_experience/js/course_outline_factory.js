(function(define) {
    'use strict';

    define([
        'jquery',
        'edx-ui-toolkit/js/utils/constants'
    ],
        function($, constants) {
            return function(root) {
                // In the future this factory could instantiate a Backbone view or React component that handles events
                $(root).keydown(function(event) {
                    var $focusable = $('.outline-item.focusable'),
                        currentFocusIndex = $.inArray(event.target, $focusable);

                    switch (event.keyCode) {  // eslint-disable-line default-case
                    case constants.keyCodes.down:
                        event.preventDefault();
                        $focusable.eq(Math.min(currentFocusIndex + 1, $focusable.length - 1)).focus();
                        break;
                    case constants.keyCodes.up:
                        event.preventDefault();
                        $focusable.eq(Math.max(currentFocusIndex - 1, 0)).focus();
                        break;
                    }
                });
            };
        }
    );
}).call(this, define || RequireJS.define);
