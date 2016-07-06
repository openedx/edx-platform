define(["jquery", "date", "js/utils/change_on_enter", "jquery.ui", "jquery.timepicker"],
function($, date, TriggerChangeEventOnEnter) {
    'use strict';
    var setupDatePicker = function (fieldName, view, index) {
        var cacheModel;
        var div;
        if (typeof index !== "undefined" && view.hasOwnProperty("collection")) {
            cacheModel = view.collection.models[index];
            div = view.$el.find('#' + view.collectionSelector(cacheModel.cid));
        } else {
            cacheModel = view.model;
            div = view.$el.find('#' + view.fieldToSelectorMap[fieldName]);
        }
        var datefield = $(div).find("input.date");
        var timefield = $(div).find("input.time");
        var cacheview = view;
        var setfield = function (event) {
            var newVal = getDate(datefield, timefield);

            // Setting to null clears the time as well, as date and time are linked.
            // Note also that the validation logic prevents us from clearing the start date
            // (start date is required by the back end).
            cacheview.clearValidationErrors();
            cacheview.setAndValidate(fieldName, (newVal || null), event);
        };

        // instrument as date and time pickers
        timefield.timepicker({'timeFormat' : 'H:i'});
        datefield.datepicker();

        // Using the change event causes setfield to be triggered twice, but it is necessary
        // to pick up when the date is typed directly in the field.
        datefield.change(setfield).keyup(TriggerChangeEventOnEnter);
        timefield.on('changeTime', setfield);
        timefield.on('input', setfield);

        var current_date = null;
        if (cacheModel) {
            current_date = cacheModel.get(fieldName);
        }
        // timepicker doesn't let us set null, so check that we have a time
        if (current_date) {
            setDate(datefield, timefield, current_date);
        } // but reset fields either way
        else {
            timefield.val('');
            datefield.val('');
        }
    };

    var getDate = function (datepickerInput, timepickerInput) {
        // given a pair of inputs (datepicker and timepicker), return a JS Date
        // object that corresponds to the datetime.js that they represent. Assume
        // UTC timezone, NOT the timezone of the user's browser.
        var date = null, time = null;
        if (datepickerInput.length > 0) {
            date = $(datepickerInput).datepicker("getDate");
        }
        if (timepickerInput.length > 0) {
            time = $(timepickerInput).timepicker("getTime");
        }
        if(date && time) {
            return new Date(Date.UTC(
                date.getFullYear(), date.getMonth(), date.getDate(),
                time.getHours(), time.getMinutes()
            ));
        } else if (date) { 
            return new Date(Date.UTC(
                date.getFullYear(), date.getMonth(), date.getDate()));
        } else {
            return null;
        }
    };

    var setDate = function (datepickerInput, timepickerInput, datetime) {
        // given a pair of inputs (datepicker and timepicker) and the date as an
        // ISO-formatted date string.
        datetime = date.parse(datetime);
        if (datetime) {
            $(datepickerInput).datepicker("setDate", datetime);
            if (timepickerInput.length > 0) {
                $(timepickerInput).timepicker("setTime", datetime);
            }
        }
    };

    var renderDate = function(dateArg) {
        // Render a localized date from an argument that can be passed to
        // the Date constructor (e.g. another Date or an ISO 8601 string)
        var date = new Date(dateArg);
        return date.toLocaleString(
            [],
            {timeZone: "UTC", timeZoneName: "short"}
        );
    };

    var parseDateFromString = function(stringDate){
        if (stringDate && typeof stringDate === "string"){
            return new Date(stringDate);
        }
        else {
            return stringDate;
        }
    };

    var convertDateStringsToObjects = function(obj, dateFields){
        for (var i = 0; i < dateFields.length; i++){
            if (obj[dateFields[i]]){
                obj[dateFields[i]] = parseDateFromString(obj[dateFields[i]]);
            }
        }
        return obj;
    };

    return {
        getDate: getDate,
        setDate: setDate,
        renderDate: renderDate,
        convertDateStringsToObjects: convertDateStringsToObjects,
        parseDateFromString: parseDateFromString,
        setupDatePicker: setupDatePicker
    };
});
