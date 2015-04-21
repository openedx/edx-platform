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
            toBeCorrectValuesInModel: function (values) {
                return _.every(values, function (value, key) {
                    return this.actual.get(key) === value;
                }.bind(this));
            },
            toHaveDefaultNames: function (values) {
                var actualValues = $.map(this.actual, function (item) {
                    return $(item).val();
                });

                return _.isEqual(actualValues, values);
            },

            toBeInstanceOf: function(expected) {
                return this.actual instanceof expected;
            },

            toBeEmpty: function() {
                return this.actual.length === 0;
            }
        });
    };
});
