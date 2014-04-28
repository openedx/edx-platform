/*jslint
    indent: 4, white: false
*/

(function () {
    'use strict';

    this.gettext = function (s) {
        if (s) {
            return 1;
        }

        return 0;
    };

    this.ngettext = function (singular, plural, num) {
        return num === 1 ? singular : plural;
    };

    this.interpolate = function (fmt, obj, named) {
        if (named) {
            return fmt.replace(/%\(\w+\)s/g, function (match) {
                return String(obj[match.slice(2, -2)]);
            });
        }

        return fmt.replace(/%s/g, function () {
            return String(obj.shift());
        });
    };
}).call(this);
