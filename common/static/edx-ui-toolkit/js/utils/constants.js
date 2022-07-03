/**
 * Reusable constants.
 */
(function(define) {
    'use strict';

    define([], function() {
        /**
         * Reusable constants.
         *
         * ### keys - A mapping of key names to their corresponding identifiers.
         * ### keyCodes - A mapping of key names to their corresponding keyCodes (DEPRECATED).
         *
         * - `constants.keys.tab` - the tab key
         * - `constants.keys.enter` - the enter key
         * - `constants.keys.esc` - the escape key
         * - `constants.keys.space` - the space key
         * - `constants.keys.left` - the left arrow key
         * - `constants.keys.up` - the up arrow key
         * - `constants.keys.right` - the right arrow key
         * - `constants.keys.down` - the down arrow key
         *
         * @class constants
         */
        return {
            keys: {
                tab: 'Tab',
                enter: 'Enter',
                esc: 'Escape',
                space: 'Space',
                left: 'ArrowLeft',
                up: 'ArrowUp',
                right: 'ArrowRight',
                down: 'ArrowDown'
            },
            // NOTE: keyCode is deprecated. Use the `key` or `code` event property if possible.
            // See: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/keyCode
            keyCodes: {
                tab: 9,
                enter: 13,
                esc: 27,
                space: 32,
                left: 37,
                up: 38,
                right: 39,
                down: 40
            }
        };
    });
}).call(
    this,
    // Pick a define function as follows:
    // 1. Use the default 'define' function if it is available
    // 2. If not, use 'RequireJS.define' if that is available
    // 3. else use the GlobalLoader to install the class into the edx namespace
    // eslint-disable-next-line no-nested-ternary
    typeof define === 'function' && define.amd ? define :
        (typeof RequireJS !== 'undefined' ? RequireJS.define :
            edx.GlobalLoader.defineAs('constants', 'edx-ui-toolkit/js/utils/constants'))
);
