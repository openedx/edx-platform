// Custom matcher library for Jasmine test assertions
// http://tobyho.com/2012/01/30/write-a-jasmine-matcher/

/* eslint-disable-next-line padded-blocks, no-undef */
define(['jquery'], function($) { // eslint-disable-line no-unused-vars

    'use strict';

    return function() {
        // eslint-disable-next-line no-undef
        jasmine.addMatchers({
            toBeCorrectValuesInModel: function() {
                // Assert the value being tested has key values which match the provided values
                return {
                    compare: function(actual, values) {
                        /* eslint-disable-next-line no-undef, no-var */
                        var passed = _.every(values, function(value, key) {
                            return actual.get(key) === value;
                        });

                        return {
                            pass: passed
                        };
                    }
                };
            }
        });
    };
});
