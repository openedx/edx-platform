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

    /* eslint-disable-next-line no-undef, no-var */
    var MAX_TIMEOUT = jasmine.DEFAULT_TIMEOUT_INTERVAL;
    // eslint-disable-next-line no-var
    var realSetTimeout = setTimeout;
    // eslint-disable-next-line no-var
    var realClearTimeout = clearTimeout;
    // eslint-disable-next-line no-undef
    jasmine.waitUntil = function(conditionalFn, maxTimeout, message) {
        // eslint-disable-next-line no-var
        var deferred = $.Deferred(),
            elapsedTimeInMs = 0,
            timeout;

        maxTimeout = maxTimeout || MAX_TIMEOUT;
        message = message || 'Timeout has expired';

        // eslint-disable-next-line no-var
        var fn = function() {
            elapsedTimeInMs += 50;
            if (conditionalFn()) {
                if (timeout) { realClearTimeout(timeout); }
                deferred.resolve();
            } else {
                if (elapsedTimeInMs >= maxTimeout) {
                    // explicitly fail the spec with the given message
                    // eslint-disable-next-line no-undef
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
