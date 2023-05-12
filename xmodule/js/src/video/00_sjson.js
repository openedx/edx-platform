(function(define) {
    define(
        'video/00_sjson.js',
        [],
        function() {
            'use strict';

            // eslint-disable-next-line no-var
            var Sjson = function(data) {
                // eslint-disable-next-line no-var
                var sjson = {
                        start: data.start.concat(),
                        text: data.text.concat()
                    },
                    // eslint-disable-next-line no-unused-vars
                    module = {};

                // eslint-disable-next-line no-var
                var getter = function(propertyName) {
                    return function() {
                        return sjson[propertyName];
                    };
                };

                // eslint-disable-next-line no-var
                var getStartTimes = getter('start');

                // eslint-disable-next-line no-var
                var getCaptions = getter('text');

                // eslint-disable-next-line no-var
                var size = function() {
                    return sjson.text.length;
                };

                function search(time, startTime, endTime) {
                    // eslint-disable-next-line no-var
                    var start = getStartTimes(),
                        max = size() - 1,
                        min = 0,
                        results,
                        index;

                    // if we specify a start and end time to search,
                    // search the filtered list of captions in between
                    // the start / end times.
                    // Else, search the unfiltered list.
                    if (typeof startTime !== 'undefined'
                && typeof endTime !== 'undefined') {
                        // eslint-disable-next-line no-use-before-define
                        results = filter(startTime, endTime);
                        start = results.start;
                        max = results.captions.length - 1;
                    } else {
                        start = getStartTimes();
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
                }

                function filter(start, end) {
                    /* filters captions that occur between inputs
             * `start` and `end`. Start and end should
             * be Numbers (doubles) corresponding to the
             * number of seconds elapsed since the beginning
             * of the video.
             *
             * Returns an object with properties
             * "start" and "captions" representing
             * parallel arrays of start times and
             * their corresponding captions.
             */
                    // eslint-disable-next-line no-var
                    var filteredTimes = [];
                    // eslint-disable-next-line no-var
                    var filteredCaptions = [];
                    // eslint-disable-next-line no-var
                    var startTimes = getStartTimes();
                    // eslint-disable-next-line no-var
                    var captions = getCaptions();

                    if (startTimes.length !== captions.length) {
                        // eslint-disable-next-line no-console
                        console.warn('video caption and start time arrays do not match in length');
                    }

                    // if end is null, then it's been set to
                    // some erroneous value, so filter using the
                    // entire array as long as it's not empty
                    if (end === null && startTimes.length) {
                        end = startTimes[startTimes.length - 1];
                    }

                    // eslint-disable-next-line no-undef
                    _.filter(startTimes, function(currentStartTime, i) {
                        if (currentStartTime >= start && currentStartTime <= end) {
                            filteredTimes.push(currentStartTime);
                            filteredCaptions.push(captions[i]);
                        }
                    });

                    return {
                        start: filteredTimes,
                        captions: filteredCaptions
                    };
                }

                return {
                    getCaptions: getCaptions,
                    getStartTimes: getStartTimes,
                    getSize: size,
                    filter: filter,
                    search: search
                };
            };

            return Sjson;
        });
}(RequireJS.define));
