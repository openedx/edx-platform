(function (root, factory) {
    factory(root, root.jQuery);
}((function () { return this; }()), function (window, $) {
    'use strict';

    /* Takes a latch function and optionally timeout and error message.
     Polls the latch function until the it returns true or the maximum timeout expires
     whichever comes first. */
    var MAX_TIMEOUT = 4500;
    jasmine.waitUntil = function (conditionalFn, maxTimeout, message) {
        var deferred = $.Deferred(),
            elapsedTimeInMs = 0,
            timeout;

        maxTimeout = maxTimeout || MAX_TIMEOUT;
        message = message || 'Timeout has expired';

        var fn = function () {
            elapsedTimeInMs += 50;

            if (conditionalFn()) {
                timeout && clearTimeout(timeout);
                deferred.resolve();
            } else {
                if (elapsedTimeInMs >= maxTimeout) {

                    // clear timeout and reject the promise
                    clearTimeout(timeout);
                    deferred.reject();

                    // explicitly fail the spec with the given message
                    fail(message);
                    return;
                }
                timeout = setTimeout(fn, 50);
            }
        };

        setTimeout(fn, 50);
        return deferred.promise();
    };
}));
