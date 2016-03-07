// Custom matcher library for Jasmine test assertions
// http://tobyho.com/2012/01/30/write-a-jasmine-matcher/

define(['jquery'], function($) { // jshint ignore:line
    'use strict';
    return function () {
        jasmine.addMatchers({
            toContainText: function () {
                return {
                    compare: function (actual, text) {
                        // Assert the value being tested has text which matches the provided text
                        var trimmedText = $.trim($(actual).text()),
                            passed;

                        if (text && $.isFunction(text.test)) {
                            passed = text.test(trimmedText);
                        } else {
                            passed = trimmedText.indexOf(text) !== -1;
                        }

                        return {
                            pass: passed
                        };
                    }
                };
            },

            toBeCorrectValuesInModel: function () {
                // Assert the value being tested has key values which match the provided values
                return {
                    compare: function (actual, values) {
                        var passed = _.every(values, function (value, key) {
                            return actual.get(key) === value;
                        }.bind(this));

                        return {
                            pass: passed
                        };
                    }
                };
            },

            toBeInstanceOf: function() {
                // Assert the type of the value being tested matches the provided type
                return {
                    compare: function (actual, expected) {
                        return {
                            pass: actual instanceof expected
                        };
                    }
                };
            }
        });
    };
});
