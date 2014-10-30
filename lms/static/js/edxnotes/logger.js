;(function (define) {
    define([], function () {
        'use strict';
        var Logger = function (id, mode) {
            this.id = id;
            this._history = [];
            // 0 - silent;
            // 1 - show logs;
            this.logLevel = mode;
        }

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

        Logger.prototype.log = function () {
            this._log('log', arguments);
        };

        Logger.prototype.error = function () {
            this._log('error', arguments);
        };

        Logger.prototype.updateHistory = function () {
            this._history.push(arguments);
        };

        Logger.prototype.getHistory = function () {
            return history;
        };

        return Logger;
    });
}).call(this, define || RequireJS.define);
