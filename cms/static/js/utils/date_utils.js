define(['jquery', 'date', 'js/utils/change_on_enter', 'jquery.ui', 'jquery.timepicker'],
function($, date, TriggerChangeEventOnEnter) {
    'use strict';

    function getDate(datepickerInput, timepickerInput, relativeTimeInput) {
        // given a set of inputs (datepicker, timepicker, and relative time picker), return a JS Date
        // object that corresponds to the datetime.js that they represent, or a float representing a relative
        // time. Assume UTC timezone, NOT the timezone of the user's browser.
        var selectedDate = null,
            selectedTime = null,
            selectedRelative = null;
        if (datepickerInput.length > 0) {
            selectedDate = $(datepickerInput).datepicker('getDate');
        }
        if (timepickerInput.length > 0) {
            selectedTime = $(timepickerInput).timepicker('getTime');
        }
        if (relativeTimeInput.length > 0) {
            selectedRelative = $(relativeTimeInput).val();
        }
        if (selectedDate && selectedRelative) {
            return null;
        }

        if (selectedDate && selectedTime) {
            return new Date(Date.UTC(
                selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate(),
                selectedTime.getHours(), selectedTime.getMinutes()
            ));
        } else if (selectedDate) {
            return new Date(Date.UTC(
                selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate()));
        } else if (selectedRelative) {
            return parseFloat(selectedRelative);
        } else {
            return null;
        }
    }

    function setDate(datepickerInput, timepickerInput, relativeTimeInput, datetime) {
        var parsedRelativeDate, parsedDatetime;

        // given a pair of inputs (datepicker and timepicker) and the date as an
        // ISO-formatted date string or a relative date formatted as +FLOAT or -FLOAT
        // where INT is a number of seconds
        if (datetime && typeof datetime === 'number') {
            parsedRelativeDate = datetime;
            if (parsedRelativeDate) {
                $(relativeTimeInput).val(parsedRelativeDate);
            }
        } else {
            parsedDatetime = Date.parse(datetime);
            if (parsedDatetime) {
                $(datepickerInput).datepicker('setDate', parsedDatetime);
                if (timepickerInput.length > 0) {
                    $(timepickerInput).timepicker('setTime', parsedDatetime);
                }
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
        var i,
            out = Object.assign({}, obj);
        for (i = 0; i < dateFields.length; i++) {
            if (obj[dateFields[i]]) {
                out[dateFields[i]] = parseDateFromString(obj[dateFields[i]]);
            }
        }
        return out;
    }

    function setupDatePicker(fieldName, view, index) {
        var cacheModel;
        var div;
        var datefield;
        var timefield;
        var relativefield;
        var cacheview;
        var setfield;
        var currentDate;
        if (typeof index !== 'undefined' && view.hasOwnProperty('collection')) {
            cacheModel = view.collection.models[index];
            div = view.$el.find('#' + view.collectionSelector(cacheModel.cid));
        } else {
            cacheModel = view.model;
            div = view.$el.find('#' + view.fieldToSelectorMap[fieldName]);
        }
        datefield = $(div).find('input.date');
        timefield = $(div).find('input.time');
        relativefield = $(div).find('input.relative');
        cacheview = view;
        setfield = function(event) {
            var newVal = getDate(datefield, timefield, relativefield);

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
        relativefield.change(setfield);

        currentDate = null;
        if (cacheModel) {
            currentDate = cacheModel.get(fieldName);
        }
        // timepicker doesn't let us set null, so check that we have a time
        if (currentDate) {
            setDate(datefield, timefield, relativefield, currentDate);
        } else {
             // but reset fields either way
            timefield.val('');
            datefield.val('');
            relativefield.val('');
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
