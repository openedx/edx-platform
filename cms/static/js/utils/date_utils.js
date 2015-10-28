define(["jquery", "date", "jquery.ui", "jquery.timepicker"], function($, date) {
    var getDate = function (datepickerInput, timepickerInput) {
        // given a pair of inputs (datepicker and timepicker), return a JS Date
        // object that corresponds to the datetime.js that they represent. Assume
        // UTC timezone, NOT the timezone of the user's browser.
        var date = $(datepickerInput).datepicker("getDate");
        var time = $(timepickerInput).timepicker("getTime");
        if(date && time) {
            return new Date(Date.UTC(
                date.getFullYear(), date.getMonth(), date.getDate(),
                time.getHours(), time.getMinutes()
            ));
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
            $(timepickerInput).timepicker("setTime", datetime);
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
        parseDateFromString: parseDateFromString
    };
});
