// Set up gettext in case it isn't available in the client runtime:
if (typeof gettext === "undefined") {
    window.gettext = function gettext_stub(string) { return string; };
    window.ngettext = function ngettext_stub(strA, strB, n) { return n === 1 ? strA : strB; };
}

// Create interpolate function in case it isn't available in the client runtime:
if (typeof interpolate === "undefined") {
    window.interpolate = function(fmt, obj, named) {
        'use strict';
        if (named) {
            return fmt.replace(/%\(\w+\)s/g, function(match) { return String(obj[match.slice(2,-2)]); });
        } else {
            return fmt.replace(/%s/g, function() { return String(obj.shift()); });
        }
    };
}
