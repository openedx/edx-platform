define(['jquery', 'date', 'js/utils/change_on_enter', 'moment-timezone', 'jquery.ui', 'jquery.timepicker'],
function($, date, TriggerChangeEventOnEnter, moment) {
    'use strict';

    function getDate(datepickerInput, timepickerInput) {
        // given a pair of inputs (datepicker and timepicker), return a JS Date
        // object that corresponds to the datetime.js that they represent. Assume
        // UTC timezone, NOT the timezone of the user's browser.
        var selectedDate = null,
            selectedTime = null;
        if (datepickerInput.length > 0) {
            selectedDate = $(datepickerInput).datepicker('getDate');
        }
        if (timepickerInput.length > 0) {
            selectedTime = $(timepickerInput).timepicker('getTime');
        }
        if (selectedDate && selectedTime) {
            return new Date(Date.UTC(
                selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate(),
                selectedTime.getHours(), selectedTime.getMinutes()
            ));
        } else if (selectedDate) {
            return new Date(Date.UTC(
                selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate()));
        } else {
            return null;
        }
    }

    function setDate(datepickerInput, timepickerInput, datetime) {
        // given a pair of inputs (datepicker and timepicker) and the date as an
        // ISO-formatted date string.
        var parsedDatetime = Date.parse(datetime);
        if (parsedDatetime) {
            $(datepickerInput).datepicker('setDate', parsedDatetime);
            if (timepickerInput.length > 0) {
                $(timepickerInput).timepicker('setTime', parsedDatetime);
            }
        }
    }

    function renderDate(dateArg) {
        // Render a localized date from an argument that can be passed to
        // the Date constructor (e.g. another Date or an ISO 8601 string)
        var dateObj = new Date(dateArg);
        return dateObj.toLocaleString(
            [],
            {timeZone: 'UTC', timeZoneName: 'short'}
        );
    }

    function parseDateFromString(stringDate) {
        if (stringDate && typeof stringDate === 'string') {
            return new Date(stringDate);
        } else {
            return stringDate;
        }
    }

    function convertDateStringsToObjects(obj, dateFields) {
        var i;
        for (i = 0; i < dateFields.length; i++) {
            if (obj[dateFields[i]]) {
                obj[dateFields[i]] = parseDateFromString(obj[dateFields[i]]);
            }
        }
        return obj;
    }

    /**
     * Calculates the utc offset in miliseconds for given
     * timezone and subtracts it from given localized time
     * to get time in UTC
     * 
     * @param {Date} localTime JS Date object in Local Time
     * @param {string} timezone IANA timezone name ex. "Australia/Brisbane"
     * @returns JS Date object in UTC
     */
    function convertLocalizedDateToUTC(localTime, timezone) {
        const localTimeMS = localTime.getTime();
        const utcOffset = moment.tz(localTime, timezone)._offset;
        return new Date(localTimeMS - (utcOffset * 60 *1000));
    }

    /**
     * Returns the timezone abbreviation for given
     * timezone name
     * 
     * @param {string} timezone IANA timezone name ex. "Australia/Brisbane"
     * @returns Timezone abbreviation ex. "AEST"
     */
    function getTZAbbreviation(timezone) {
        return moment(new Date()).tz(timezone).format('z');
    }

    /**
     * Converts the given datetime string from UTC to localized time
     * 
     * @param {string} utcDateTime JS Date object with UTC datetime
     * @param {string} timezone IANA timezone name ex. "Australia/Brisbane"
     * @returns Formatted datetime string with localized timezone
     */
    function getLocalizedCurrentDate(utcDateTime, timezone) {
        const localDateTime = moment(utcDateTime).tz(timezone);
        return localDateTime.format('YYYY-MM-DDTHH[:]mm[:]ss');
    }

    function setupDatePicker(fieldName, view, index) {
        var cacheModel;
        var div;
        var datefield;
        var timefield;
        var tzfield;
        var cacheview;
        var setfield;
        var currentDate;
        var timezone;
        if (typeof index !== 'undefined' && view.hasOwnProperty('collection')) {
            cacheModel = view.collection.models[index];
            div = view.$el.find('#' + view.collectionSelector(cacheModel.cid));
        } else {
            cacheModel = view.model;
            div = view.$el.find('#' + view.fieldToSelectorMap[fieldName]);
        }
        datefield = $(div).find('input.date');
        timefield = $(div).find('input.time');
        tzfield = $(div).find('span.timezone');
        cacheview = view;
        
        timezone = cacheModel.get('user_timezone');

        setfield = function(event) {
            var newVal = getDate(datefield, timefield);

            if (timezone) {
                newVal = convertLocalizedDateToUTC(newVal, timezone);
            }

            // Setting to null clears the time as well, as date and time are linked.
            // Note also that the validation logic prevents us from clearing the start date
            // (start date is required by the back end).
            cacheview.clearValidationErrors();
            cacheview.setAndValidate(fieldName, (newVal || null), event);
        };

        // instrument as date and time pickers
        timefield.timepicker({timeFormat: 'H:i'});
        datefield.datepicker();

        // Using the change event causes setfield to be triggered twice, but it is necessary
        // to pick up when the date is typed directly in the field.
        datefield.change(setfield).keyup(TriggerChangeEventOnEnter);
        timefield.on('changeTime', setfield);
        timefield.on('input', setfield);

        currentDate = null;
        if (cacheModel) {
            currentDate = cacheModel.get(fieldName);
        }

        if (timezone) {
            const tz = getTZAbbreviation(timezone);
            $(tzfield).text("("+tz+")");
        }

        // timepicker doesn't let us set null, so check that we have a time
        if (currentDate) {
            if (timezone) {
                currentDate = getLocalizedCurrentDate(currentDate, timezone);
            }
            setDate(datefield, timefield, currentDate);
        } else {
             // but reset fields either way
            timefield.val('');
            datefield.val('');
        }
    }

    return {
        getDate: getDate,
        setDate: setDate,
        renderDate: renderDate,
        convertDateStringsToObjects: convertDateStringsToObjects,
        parseDateFromString: parseDateFromString,
        setupDatePicker: setupDatePicker
    };
});
