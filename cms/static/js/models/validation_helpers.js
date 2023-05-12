/**
 * Provide helper methods for modal validation.
*/
// eslint-disable-next-line no-undef
define(['jquery'],
    // eslint-disable-next-line no-unused-vars
    function($) {
        // eslint-disable-next-line no-var
        var validateIntegerRange = function(attributeVal, range) {
            // Validating attribute should have an integer value and should be under the given range.
            // eslint-disable-next-line no-var
            var isIntegerUnderRange = true;
            // eslint-disable-next-line no-var
            var value = Math.round(attributeVal); // see if this ensures value saved is int
            if (!isFinite(value) || /\D+/.test(attributeVal) || value < range.min || value > range.max) {
                isIntegerUnderRange = false;
            }
            return isIntegerUnderRange;
        };

        return {
            validateIntegerRange: validateIntegerRange
        };
    });
