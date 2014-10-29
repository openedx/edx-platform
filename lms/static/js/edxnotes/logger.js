;(function (define) {
    define([], function () {
        var Logger = function (mode) {
            this._history = [];
            // 0 - silent;
            // 1 - show logs;
            this.logLevel = mode;
        }

        Logger.prototype._log = function (logType, args) {
            this.updateHistory.apply(this, arguments);
            if (this.logLevel && console && console[logType]) {
                if (console[logType].apply){
                    // Do this for normal browsers
                    console[logType].apply(console, args);
                } else {
                    // Do this for IE
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
}).call(this, RequireJS.define);
