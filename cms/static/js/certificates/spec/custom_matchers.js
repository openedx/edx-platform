// Custom matcher library for Jasmine test assertions
// http://tobyho.com/2012/01/30/write-a-jasmine-matcher/

define(['jquery'], function($) { // jshint ignore:line
    'use strict';
    return function (that) {
        that.addMatchers({

            toContainText: function (text) {
                // Assert the value being tested has text which matches the provided text
                var trimmedText = $.trim($(this.actual).text());
                if (text && $.isFunction(text.test)) {
                    return text.test(trimmedText);
                } else {
                    return trimmedText.indexOf(text) !== -1;
                }
            },

            toBeCorrectValuesInModel: function (values) {
                // Assert the value being tested has key values which match the provided values
                return _.every(values, function (value, key) {
                    return this.actual.get(key) === value;
                }.bind(this));
            },

            toBeInstanceOf: function(expected) {
                // Assert the type of the value being tested matches the provided type
                return this.actual instanceof expected;
            }
        });
    };
});
