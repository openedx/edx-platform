;(function (define) {
    define([], function () {
        'use strict';
        /**
         * Logger constructor.
         * @constructor
         * @param {String} id Id of the logger.
         * @param {Boolean|Number} mode Outputs messages to the Web Console if true.
         */
        var Logger = function (id, mode) {
            this.id = id;
            this._history = [];
            // 0 - silent;
            // 1 - show logs;
            this.logLevel = mode;
        }

        /**
         * Outputs a message with appropriate type to the Web Console and
         * store it in the history.
         * @param  {String} logType The type of the log message.
         * @param  {Arguments} args Information that will be stored.
         */
        Logger.prototype._log = function (logType, args) {
            this.updateHistory.apply(this, arguments);
            // Adds ID at the first place
            Array.prototype.unshift.call(args, this.id);
            if (this.logLevel && console && console[logType]) {
                if (console[logType].apply){
                    console[logType].apply(console, args);
                } else { // Do this for IE
                    console[logType](args.join(' '));
                }
            }
        };

        /**
         * Outputs a message to the Web Console and store it in the history.
         */
        Logger.prototype.log = function () {
            this._log('log', arguments);
        };

        /**
         * Outputs an error message to the Web Console and store it in the history.
         */
        Logger.prototype.error = function () {
            this._log('error', arguments);
        };

        /**
         * Adds information to the history.
         */
        Logger.prototype.updateHistory = function () {
            this._history.push(arguments);
        };

        /**
         * Returns the history for the logger.
         * @return {Array}
         */
        Logger.prototype.getHistory = function () {
            return this._history;
        };

        return Logger;
    });
}).call(this, define || RequireJS.define);
