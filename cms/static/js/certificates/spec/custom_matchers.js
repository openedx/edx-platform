// Custom matcher library for Jasmine test assertions
// http://tobyho.com/2012/01/30/write-a-jasmine-matcher/

define(['jquery'], function($) { // jshint ignore:line
    'use strict';
    return function () {
        jasmine.addMatchers({
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
            }
        });
    };
});
