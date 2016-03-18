(function () {
    'use strict';

    jasmine.waitForInputAjax = function (conditionalFn, maxTimeout) {
        var deferred = $.Deferred(),
            elapsedTimeInMs = 0,
            timeout;

        var fn = function () {
            elapsedTimeInMs += 50;

            if (conditionalFn()) {
                timeout && clearTimeout(timeout);
                deferred.resolve();
            } else {
                if (elapsedTimeInMs >= maxTimeout) {
                    deferred.reject();
                    clearTimeout(timeout);
                    return;
                }

                timeout = setTimeout(fn, 50);
            }
        };

        setTimeout(fn, 50);
        return deferred.promise();
    };

}).call(this);
