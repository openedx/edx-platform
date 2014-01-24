window.gettext = function(s){return s;};
window.ngettext = function(singular, plural, num){ return num == 1 ? singular : plural }

function interpolate(fmt, obj, named) {
    if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
    } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())});
    }
}
