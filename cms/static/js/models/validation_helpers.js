/**
 * Provide helper methods for modal validation.
*/
define(['jquery'],
    function($) {
        var validateIntegerRange = function(attributeVal, range) {
            // Validating attribute should have an integer value and should be under the given range.
            var isIntegerUnderRange = true;
            var value = Math.round(attributeVal); // see if this ensures value saved is int
            if (!isFinite(value) || /\D+/.test(attributeVal) || value < range.min || value > range.max) {
                isIntegerUnderRange = false;
            }
            return isIntegerUnderRange;
        };

        return {
            'validateIntegerRange': validateIntegerRange
        };
    });
