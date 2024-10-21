/**
 *
 * A helper function to utilize DateUtils quickly in display templates.
 *
 * @param: {string} data-datetime A pre-localized datetime string, assumed to be in UTC.
 * @param: {string} lang The user's preferred language.
 * @param: {string} data-timezone (optional) A user-set timezone preference.
 * @param: {object} data-format (optional) a format constant as defined in DataUtil.dateFormatEnum.
 * @param: {string} data-string (optional) a string for parsing through StringUtils after localizing
 * datetime
 *
 * @return: {string} a user-time, localized, formatted datetime string
 *
 */

(function (define) {
  "use strict";

  define([
    "jquery",
    "edx-ui-toolkit/js/utils/date-utils",
    "edx-ui-toolkit/js/utils/string-utils",
    "moment", // Ensure moment is included
    "moment-timezone", // Ensure moment-timezone is included
  ], function ($, DateUtils, StringUtils) {
    var DateUtilFactory;
    var localizedTime;
    var stringHandler;
    var displayDatetime;
    var isValid;
    var transform;
    var dueDateFormat;
    var dateFormat;

    dueDateFormat = Object.freeze({
      "%Y-%d-%m": "YYYY, D MMM HH:mm [GMT]ZZ", // example: 2018, 01 Jan 15:30 GMT+0000
      "%m-%d-%Y": "MMM D, YYYY, HH:mm [GMT]ZZ", // example: Jan 01, 2018, 15:30 GMT+0000
      "%d-%m-%Y": "D MMM YYYY, HH:mm [GMT]ZZ", // example: 01 Jan, 2018, 15:30 GMT+0000
      "%Y-%m-%d": "YYYY, MMM D HH:mm [GMT]ZZ", // example: 2018, Jan 01 15:30 GMT+0000
    });

    transform = function (iterationKey) {
      var context;
      $(iterationKey).each(function () {
        if (isValid($(this).data("datetime"))) {
          dateFormat = DateUtils.dateFormatEnum[$(this).data("format")];
          if (typeof dateFormat === "undefined") {
            dateFormat = dueDateFormat[$(this).data("format")];
          }
          context = {
            datetime: $(this).data("datetime"),
            timezone: $(this).data("timezone"),
            language: $(this).data("language"),
            format: dateFormat,
          };
          displayDatetime = stringHandler(localizedTime(context), $(this).data("string"), $(this).data("datetoken"));
          $(this).text(displayDatetime);
        } else {
          displayDatetime = stringHandler($(this).data("string"));
          $(this).text(displayDatetime);
        }
      });
    };

    localizedTime = function (context) {
      function formatTimeInTimezone(dateTime, timeZone = "UTC") {
        const options = {
          year: "numeric",
          month: "short", // 'short' gives the abbreviated month name (e.g., "Aug")
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          hour12: false, // 24-hour format (set to `true` for 12-hour format)
          timeZone: timeZone, // Specify the desired timezone (e.g., CST)
          timeZoneName: "short", // Include the short timezone abbreviation (CST, PDT, etc.)
        };

        const formattedTime = new Intl.DateTimeFormat(context.language, options).format(new Date(dateTime));
        return formattedTime;
      }
      return formatTimeInTimezone(context.datetime, context.timezone);
      // Output: "Aug 1, 2024, 02:30 CST"
    };

    stringHandler = function (localTimeString, containerString, token) {
      var returnString;
      var interpolateDict = {};
      var dateToken;
      if (isValid(token)) {
        dateToken = token;
      } else {
        dateToken = "date";
      }
      interpolateDict[dateToken] = localTimeString;

      if (isValid(containerString)) {
        returnString = StringUtils.interpolate(containerString, interpolateDict);
      } else {
        returnString = localTimeString;
      }
      return returnString;
    };

    isValid = function (candidateVariable) {
      return (
        candidateVariable !== undefined &&
        candidateVariable !== "" &&
        candidateVariable !== "Invalid date" &&
        candidateVariable !== "None"
      );
    };
    DateUtilFactory = {
      transform: transform,
      stringHandler: stringHandler,
    };
    return DateUtilFactory;
  });
}).call(this, define || RequireJS.define);
