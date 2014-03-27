(function (define) {

define(
'video/00_sjson.js',
[],
function() {
"use strict";

    var Sjson = function (data) {
        var sjson = {
                start: data.start.concat(),
                text: data.text.concat()
            },
            module = {};

        var getter = function (propertyName) {
            return function () {
                return sjson[propertyName];
            };
        };

        var getStartTimes = getter('start');

        var getCaptions = getter('text');

        var size = function () {
            return sjson.text.length;
        };

        var search = function (time) {
            var start = getStartTimes(),
                max = size() - 1,
                min = 0,
                index;

            if (time < start[min]) {
                return -1;
            }
            while (min < max) {
                index = Math.ceil((max + min) / 2);

                if (time < start[index]) {
                    max = index - 1;
                }

                if (time >= start[index]) {
                    min = index;
                }
            }

            return min;
        };

        return {
            getCaptions: getCaptions,
            getStartTimes: getStartTimes,
            getSize: size,
            search: search
        };
    };

    return Sjson;
});
}(RequireJS.define));

