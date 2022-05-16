/* eslint-env node */

// Takes a latch function and optionally timeout and error message.
// Polls the latch function until the it returns true or the maximum timeout expires
// whichever comes first.
(function(root, factory) {
    factory(root, root.jQuery);
}((function() {
    return this;
}()), function(window, $) {
    'use strict';

    var MAX_TIMEOUT = jasmine.DEFAULT_TIMEOUT_INTERVAL;
    var realSetTimeout = setTimeout;
    var realClearTimeout = clearTimeout;
    jasmine.waitUntil = function(conditionalFn, maxTimeout, message) {
        var deferred = $.Deferred(),
            elapsedTimeInMs = 0,
            timeout;

        maxTimeout = maxTimeout || MAX_TIMEOUT;
        message = message || 'Timeout has expired';

        var fn = function() {
            elapsedTimeInMs += 50;
            if (conditionalFn()) {
                if (timeout) { realClearTimeout(timeout); }
                deferred.resolve();
            } else {
                if (elapsedTimeInMs >= maxTimeout) {
                    // explicitly fail the spec with the given message
                    fail(message);

                    // clear timeout and reject the promise
                    realClearTimeout(timeout);
                    deferred.reject();

                    return;
                }
                timeout = realSetTimeout(fn, 50);
            }
        };

        realSetTimeout(fn, 50);
        return deferred.promise();
    };
}));
