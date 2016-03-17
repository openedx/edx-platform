(function () {
    'use strict';

    jasmine.waitForInputAjax = function (conditionalFn) {
        var deferred = $.Deferred(),
            timeout;

        var fn = function () {
            if (conditionalFn()) {
                timeout && clearTimeout(timeout);
                deferred.resolve();
            } else {
                timeout = setTimeout(fn, 50);
            }
        };

        setTimeout(fn, 50);
        return deferred.promise();
    };

}).call(this);
