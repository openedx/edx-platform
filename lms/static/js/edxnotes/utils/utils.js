;(function (define, undefined) {
'use strict';
define([], function($, _) {
    /**
     * Replaces all newlines in a string by HTML line breaks.
     * @param {String} str The input string.
     * @return `String` with '<br>' instead all newlines (\r\n, \n\r, \n and \r).
     * @example
     *   nl2br("This\r\nis\n\ra\nstring\r")
     *   Output:
     *   This<br>
     *   is<br>
     *   a<br>
     *   string<br>
     */
    var nl2br = function (str) {
        return (str + '').replace(/(\r\n|\n\r|\r|\n)/g, '<br>');
    }

    return {
        nl2br: nl2br
    };
});
}).call(this, define || RequireJS.define);
