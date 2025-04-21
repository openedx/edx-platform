import _ from 'underscore';

/**
 * Creates an object to manage subtitle data.
 *
 * @param {object} data An object containing subtitle information with `start` (array of start times) and `text` (array of captions).
 * @returns {object} An object with methods to access and manipulate subtitle data.
 */
const Sjson = function (data) {
    'use strict';

    const sjson = {
        start: Array.isArray(data.start) ? [...data.start] : [],
        text: Array.isArray(data.text) ? [...data.text] : []
    };

    /**
     * Creates a getter function for a specified property of the `sjson` object.
     *
     * @param {string} propertyName The name of the property to access ('start' or 'text').
     * @returns {function(): Array} A function that returns a copy of the specified array.
     */
    const getter = function (propertyName) {
        return function () {
            return [...sjson[propertyName]];
        };
    };

    /**
     * Returns a copy of the array of start times.
     *
     * @returns {Array<number>} An array of subtitle start times in seconds.
     */
    const getStartTimes = getter('start');

    /**
     * Returns a copy of the array of captions.
     *
     * @returns {Array<string>} An array of subtitle text.
     */
    const getCaptions = getter('text');

    /**
     * Returns the number of captions available.
     *
     * @returns {number} The total number of captions.
     */
    const size = function () {
        return sjson.text.length;
    };

    /**
     * Searches for the index of the caption that should be displayed at a given time.
     *
     * @param {number} time The time (in seconds) to search for.
     * @param {number} [startTime] An optional start time (in seconds) to filter the search within.
     * @param {number} [endTime] An optional end time (in seconds) to filter the search within.
     * @returns {number} The index of the caption to display at the given time, or the index of the last caption if the time is beyond the last start time. Returns 0 if no captions are available.
     */
    function search(time, startTime, endTime) {
        let start = getStartTimes();
        let max = size() - 1;
        let min = 0;
        let searchResults;
        let index;

        if (typeof startTime !== 'undefined' && typeof endTime !== 'undefined') {
            searchResults = filter(startTime, endTime);
            start = searchResults.start;
            max = searchResults.captions.length - 1;
        }

        if (start.length === 0) {
            return 0;
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

    /**
     * Filters captions that occur between a given start and end time.
     *
     * @param {number} start The start time (in seconds) for filtering.
     * @param {number} end The end time (in seconds) for filtering.
     * @returns {object} An object with `start` (array of filtered start times) and `captions` (array of corresponding filtered captions).
     */
    function filter(start, end) {
        const filteredTimes = [];
        const filteredCaptions = [];
        const startTimes = getStartTimes();
        const captions = getCaptions();

        if (startTimes.length !== captions.length) {
            console.warn('video caption and start time arrays do not match in length');
        }

        let effectiveEnd = end;
        if (effectiveEnd === null && startTimes.length) {
            effectiveEnd = startTimes[startTimes.length - 1];
        }

        for (let i = 0; i < startTimes.length; i++) {
            const currentStartTime = startTimes[i];
            if (currentStartTime >= start && currentStartTime <= effectiveEnd) {
                filteredTimes.push(currentStartTime);
                filteredCaptions.push(captions[i]);
            }
        }

        return {
            start: filteredTimes,
            captions: filteredCaptions
        };
    }

    return {
        getCaptions,
        getStartTimes,
        getSize: size,
        filter,
        search
    };
};

export { Sjson };