define(['jquery'], function($) {
    'use strict';
    return function (that) {
        jasmine.addMatchers({
            toContainText: function () {
                return {
                    compare: function (actual, text) {
                        var result = {},
                            trimmedText = $.trim($(actual).text());

                        if (text && $.isFunction(text.test)) {
                            result.pass = text.test(trimmedText);
                        } else {
                            result.pass = trimmedText.indexOf(text) !== -1;
                        }

                        return result;
                    }
                };
            },

            toHaveLength: function () {
                return {
                    compare: function (actual, expected) {
                        return {
                            pass: $(actual).length === expected
                        }
                    }
                };
            },

            toHaveIndex: function () {
                return {
                    compare: function (actual, expected) {
                        return {
                            pass: $(actual).index() === expected
                        }
                    }
                };
            },

            //toBeInRange: function (min, max) {
            //    return min <= this.actual && this.actual <= max;
            //},

            toBeFocused: function () {
                return {
                    compare: function (actual, expected) {
                        return {
                            pass: $(actual)[0] === $(actual)[0].ownerDocument.activeElement
                        }
                    }
                };
            }
        });
    };
});
