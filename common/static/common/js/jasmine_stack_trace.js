/* This file overrides ExceptionFormatter of jasmine before it's initialization in karma-jasmine's
 boot.js. It's important because ExceptionFormatter returns a constructor function. Once the method has been
 initialized we can't override the ExceptionFormatter as Jasmine then uses the stored reference to the function */
(function () {
    /* globals jasmineRequire */
    'use strict';

    var OldExceptionFormatter = jasmineRequire.ExceptionFormatter(),
        oldExceptionFormatter = new OldExceptionFormatter(),
        MAX_STACK_TRACE_LINES = 10;

    jasmineRequire.ExceptionFormatter = function () {
        function ExceptionFormatter() {
            this.message = oldExceptionFormatter.message;
            this.stack = function (error) {
                var errorMsg = null;

                if (error) {
                    errorMsg = error.stack.split('\n').slice(0, MAX_STACK_TRACE_LINES).join('\n');
                }

                return errorMsg;
            };
        }

        return ExceptionFormatter;
    };
}());
