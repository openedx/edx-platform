(function (define) {
'use strict';
define(
'video/00_i18n.js',
[],
function() {
    /**
     * i18n module.
     * @exports video/00_i18n.js
     * @return {object}
     */

    return {
        'Volume': gettext('Volume'),
        // Translators: Volume level equals 0%.
        'Muted': gettext('Muted'),
        // Translators: Volume level in range ]0,20]%
        'Very low': gettext('Very low'),
        // Translators: Volume level in range ]20,40]%
        'Low': gettext('Low'),
        // Translators: Volume level in range ]40,60]%
        'Average': gettext('Average'),
        // Translators: Volume level in range ]60,80]%
        'Loud': gettext('Loud'),
        // Translators: Volume level in range ]80,99]%
        'Very loud': gettext('Very loud'),
        // Translators: Volume level equals 100%.
        'Maximum': gettext('Maximum')
    };
});
}(RequireJS.define));
