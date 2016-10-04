
/**
 *
 * A helper function to utilize DateUtils quickly in iterative display templates
 *
 * @param: {string} data-datetime pre-localized date, in UTC
 * @param: {string} data-time_zone (optional) user-set timezone preference.
 * @param: {string} lang The user's preferred language.
 * @param: {object} data-format (optional) a format constant as defined in DataUtil.dateFormatEnum.
 *
 * @param: {string} data-string (optional) ugettext-able string
 *
 * Localized according to preferences first, local data second.
 * Default to UTC/en-US Display if error/unknown.
 *
 * @return: {string} a user-time, localized, formatted datetime string
 *
 */

(function(define) {
    'use strict';

    define([
        'jquery',
        'edx-ui-toolkit/js/utils/date-utils',
        'edx-ui-toolkit/js/utils/string-utils'
    ], function(
        $,
        DateUtils,
        StringUtils
        ) {
        return function() {
            var displayTime;
            var displayString;
            $('.localized-datetime').each(function() {
                if ($(this).data('datetime') !== 'None' && $(this).data('datetime') !== undefined) {
                    var context = {
                        datetime: $(this).data('datetime'),
                        timezone: $(this).data('timezone'),
                        language: $(this).attr('lang'),
                        format: $(this).data('format')
                    }
                    displayTime = DateUtils.localize(context);
                }
            if ($(this).data('string') !== undefined && $(this).data('string').length > 0) {
                displayString = StringUtils.interpolate(
                    '{string} {date}',
                    {
                        string: $(this).data('string'),
                        date: displayTime
                    }
                );
            } else {
                displayString = displayTime;
            }
            if (displayTime && displayString.length > 0) {

                console.log(displayString);
                /*
                 uncomment out the following line once approved
                 */
                // $(this).text(displayString);
            }
            });
        };
    });
}).call(this, define || RequireJS.define);

