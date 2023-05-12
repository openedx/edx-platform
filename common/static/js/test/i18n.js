window.gettext = function(s) { return s; };
// eslint-disable-next-line eqeqeq
window.ngettext = function(singular, plural, num) { return num == 1 ? singular : plural; };

// eslint-disable-next-line no-unused-vars
function interpolate(fmt, obj, named) {
    if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match) { return String(obj[match.slice(2, -2)]); });
    } else {
        // eslint-disable-next-line no-unused-vars
        return fmt.replace(/%s/g, function(match) { return String(obj.shift()); });
    }
}
