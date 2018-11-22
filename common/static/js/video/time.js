(function(define) {
    'use strict';
    define(
'js/video/time.js',
['underscore'],
function(_) {
    /**
     * Provides time formatting and conversion functions.
     */

    function pad(number) {
        if (number < 10) {
            return '0' + number;
        } else {
            return '' + number;
        }
    }

    function format(time, fullFormat) {
        var hours, minutes, seconds;

        if (!_.isFinite(time) || time < 0) {
            seconds = Math.floor(0);
        } else {
            seconds = Math.floor(time);
        }

        minutes = Math.floor(seconds / 60);
        hours = Math.floor(minutes / 60);
        seconds = seconds % 60;
        minutes = minutes % 60;

        if (fullFormat) {
            return '' + pad(hours) + ':' + pad(minutes) + ':' + pad(seconds % 60);
        } else if (hours) {
            return '' + hours + ':' + pad(minutes) + ':' + pad(seconds % 60);
        } else {
            return '' + minutes + ':' + pad(seconds % 60);
        }
    }

    function formatFull(time) {
        // The returned value will not be user-facing. So no need for
        // internationalization.
        return format(time, true);
    }

    function convert(time, oldSpeed, newSpeed) {
        return (time * oldSpeed / newSpeed).toFixed(3);
    }

    return {
        format: format,
        formatFull: formatFull,
        convert: convert
    };
});
}(RequireJS.define));
