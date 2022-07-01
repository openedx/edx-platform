/**
 * Create a formatted, locale-aware string representation of a datetime.
 *
 * This module contains general purpose functions for localizing and displaying
 * date-times by timezone, locale and preferred language."
 *
 * Most of the heavy lifting is done by the {@link http://momentjs.com/ |'moments' js library}
 * with the moment-with-locales and moment-timezones add-ons.
 *
 *
 *
 * Example:
 *
 *~~~ javascript
 * var context = {
 *    datetime: '2016-10-14 08:00:00+00:00',
 *    timezone: 'Pacific/Kiritimati',
 *    language: 'ar',
 *    format: DateUtils.dateFormats.shortDate
 * };
 * localized_date = DateUtils.localize(context);
 *~~~
 *
 * @module DateUtils
 */


(function(define) {
    'use strict';

    define([
        'jquery',
        'moment',
        'moment-timezone'
    ], function(
        $,
        moment,
        momentTZ
        ) {
        var DateUtils,
            localize,
            stringToMoment,
            localizeTime,
            getSysTimezone,
            getDisplayTime,
            getDisplayLang,
            getDisplayFormat,
            isValid;

        var dateFormatEnum = Object.freeze({
            shortDate: 'll', // example: Jan 01, 2016
            longDate: 'LLLL', // example: Friday, January 01, 2016
            time: 'LTS z', // example: 15:30:32 UTC
            defaultFormat: 'll HH[:]mm z', // example: Jan 01, 2016 15:30 UTC
            defaultWithParen: 'll HH[:]mm (z)', // example: Jan 01, 2016 15:30 (UTC)
            longDateTime: 'dddd, ll HH[:]mm z' // example: Friday, Jan 01, 2016 15:30 UTC
        });

        var DEFAULT_LANG = 'en';
        var DEFAULT_TIMEZONE = 'UTC';
        var DEFAULT_FORMAT = dateFormatEnum.defaultFormat;

        /**
         *
         * Renders a localized date/time in a standard format.
         *
         * @param context
         *
         * - datetime: {string} The (UTC) datetime server-side string.
         * - timezone: {string} (optional) the user set time zone preference, or 'None' if unset.
         * This should be in a format like 'Region/Locale', e.g. 'Atlantic/Azores'. Defaults to 'UTC'.
         * - language: {string} (optional), the user set language, an ISO 639-1 language string, defaults to 'en'
         * - format: {object} (optional), a format constant. Defaults to DEFAULT_FORMAT.
         *
         * @returns {string} A formatted, timezone-offset, internationalized date and time.
         *
         */
        localize = function(context) {
            var localTime;
            var displayTime = '';

            if (isValid(context.datetime)) {
                localTime = localizeTime(
                    DateUtils.stringToMoment(context.datetime),
                    context.timezone
                );
                displayTime = getDisplayTime(localTime, context.language, context.format);
            }
            return displayTime;
        };

        /**
         * Converts a string to mutable 'moment' datetime object.
         *
         * The input datetimeString can be just a date, a date and time,
         * or a complex date/time string with TZ offset. This is fairly wide-open, as
         * many strings will satisfy this requirement.
         * (e.g. 01-01-16 and Jan 1, 2016, and 2016-01-01 01:00:00+00:00 will work)
         *
         * The recommendation is to use a fully informed string, e.g. '2016-01-01 01:00:00+00:00',
         * to limit possible date, time, and timezone ambiguities.
         *
         * @param {string} datetimeString. A string representation of a datetime.
         * @returns {object} A moment.js UTC datetime object.
         *
        */
        stringToMoment = function(datetimeString) {
            var utcDateObject;
            if (isValid(datetimeString)) {
                utcDateObject = moment(datetimeString).utc();
            } else {
                utcDateObject = undefined;
            }
            return utcDateObject;
        };

        /**
         *
         * Returns a new time that is offset by the requested timezone.
         *
         * @param {Object} dateTimeObject A moment.js datetime object.
         * @param {string} timezone A timezone representation, e.g. 'America/New_York'.
         * @return {object} A moment.js datetime object in a determined timezone.
         */
        localizeTime = function(dateTimeObject, timezone) {
            var localTime;
            if (isValid(dateTimeObject) && isValid(timezone)) {
                localTime = dateTimeObject.tz(timezone);
            } else if (isValid(dateTimeObject)) {
                localTime = dateTimeObject.tz(getSysTimezone());
            } else {
                localTime = '';
            }
            return localTime;
        };

        /**
         *
         * Helper function to determine system timezone, and fallback to UTC
         * Determines timezone from argument, falling back to system/browser settings, then UTC.
         *
         * @return {string} Will attempt to return a determined timezone string, with a fallback to UTC.
         *
         */
        getSysTimezone = function() {
            var timezone = momentTZ.tz.guess();
            if (!isValid(timezone)) {
                timezone = DEFAULT_TIMEZONE;
            }
            return timezone;
        };

        /**
         *
         * Generate a timezone-aware and language-aware string.
         *
         * This includes a param for standard formatting constants.
         *
         * Browser preferred language is currently overridden by platform-set language preference.
         * If no preference is set, the function attempts to determine the locale settings
         * (e.g. en-US) from the browser preferences.
         *
         * This function will default to UTC/en-US display in default format in the case of
         * an unresolvable language or timezone
         *
         * preferred_language = 'en' yields Oct. 14, 2016 09:00 BST
         *
         * preferred_language = 'ru' yields 14 окт 2016 г. 09:00 BST
         *
         * @param {object} localTime A moment.js datetime object offset to a determined timezone.
         * @param {string} language an ISO 639-1 language code (e.g. 'en-US', 'fr')
         * @param {object} format (optional) A desired date format, via the dateFormatEnum.
         * @return {string} A language/timezone aware localized string
        */
        getDisplayTime = function(localTime, language, format) {
            var displayTime = '';
            var displayLang = getDisplayLang(language);
            var displayFormat = getDisplayFormat(format);

            if (isValid(displayLang) && isValid(displayFormat)) {
                if (moment(localTime).isValid()) {
                    displayTime = localTime.locale(displayLang).format(displayFormat);
                }
            }
            return displayTime;
        };

        /**
         * Helper function to determine sys/browser language (if unpassed)
         *
         * @param {string} language (optional) an ISO 639-1 language code (e.g. 'en-US', 'fr')
         * @returns {string} an ISO 639-1 language code (e.g. 'en-US', 'fr')
         */
        getDisplayLang = function(language) {
            var displayLang;
            if (isValid(language)) {
                displayLang = language;
            } else {
                displayLang = window.navigator.userLanguage || window.navigator.language;
            }
            // default
            if (isValid(language)) {
                return displayLang;
            } else {
                return DEFAULT_LANG;
            }
        };

        /**
         * Helper function to determine format constant.
         *
         * Defaults to DEFAULT_FORMAT if malformed or unpassed.
         *
         * @param {object} format (optional) A format constant.
         * @returns {string} A format constant.
         */
        getDisplayFormat = function(format) {
            var displayFormat = DEFAULT_FORMAT;
            if (isValid(format)) {
                displayFormat = format;
            }
            return displayFormat;
        };

        /**
         * Helper function to determine variable/context validity.
         *
         * @param {string} candidateVariable to test
         * @returns {boolean}
         */
        isValid = function(candidateVariable) {
            return candidateVariable !== undefined
                && candidateVariable !== ''
                && candidateVariable !== 'Invalid date'
                && candidateVariable !== 'None';
        };

        DateUtils = {
            dateFormatEnum: dateFormatEnum,
            localize: localize,
            stringToMoment: stringToMoment,
            getSysTimezone: getSysTimezone,
            localizeTime: localizeTime
        };
        return DateUtils;
    });
}).call(
    this,
    // Pick a define function as follows:
    // 1. Use the default 'define' function if it is available
    // 2. If not, use 'RequireJS.define' if that is available
    // 3. else use the GlobalLoader to install the class into the edx namespace
    // eslint-disable-next-line no-nested-ternary
    typeof define === 'function' && define.amd ? define :
        (typeof RequireJS !== 'undefined' ? RequireJS.define :
            edx.GlobalLoader.defineAs('DateUtils', 'edx-ui-toolkit/js/utils/date-utils'))
);

