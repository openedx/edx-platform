define(['jquery'], function($) {
    'use strict';
    return function (that) {
        that.addMatchers({
            toContainText: function (text) {
                var trimmedText = $.trim($(this.actual).text());

                if (text && $.isFunction(text.test)) {
                  return text.test(trimmedText);
                } else {
                  return trimmedText.indexOf(text) !== -1;
                }
            },

            toHaveLength: function (number) {
                return $(this.actual).length === number;
            },

            toHaveIndex: function (number) {
                return $(this.actual).index() === number;
            },

            toBeInRange: function (min, max) {
                return min <= this.actual && this.actual <= max;
            }
        });
    };
});
