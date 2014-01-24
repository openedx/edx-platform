define(["jquery", "jquery.ui", "jquery.timepicker"], function($) {
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
    return getDate;
});
