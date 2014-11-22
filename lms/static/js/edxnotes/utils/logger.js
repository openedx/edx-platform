;(function (define) {
'use strict';
define([], function () {
    var loggers = [],
        Logger, now, destroyLogger;

    now = function () {
        if (performance && performance.now) {
            return performance.now();
        } else if (Date.now) {
            return Date.now();
        } else {
            return (new Date()).getTime();
        }
    };

    /**
     * Removes a reference on the logger from `loggers`.
     * @param  {Object} logger An instance of Logger.
     */
    destroyLogger = function (logger) {
        var index = loggers.length,
            removedLogger;

        while(index--) {
            if (loggers[index].id === logger.id) {
                removedLogger = loggers.splice(index, 1)[0];
                removedLogger.historyStorage = [];
                removedLogger.timeStorage = {};
                break;
            }
        }
    };

    /**
     * Logger constructor.
     * @constructor
     * @param {String} id Id of the logger.
     * @param {Boolean|Number} mode Outputs messages to the Web Console if true.
     */
    Logger = function (id, mode) {
        this.id = id;
        this.historyStorage = [];
        this.timeStorage = {};
        // 0 - silent;
        // 1 - show logs;
        this.logLevel = mode;
    };

    /**
     * Outputs a message with appropriate type to the Web Console and
     * store it in the history.
     * @param  {String} logType The type of the log message.
     * @param  {Arguments} args Information that will be stored.
     */
    Logger.prototype._log = function (logType, args) {
        if (!this.logLevel) {
            return false;
        }
        this.updateHistory.apply(this, arguments);
        // Adds ID at the first place
        Array.prototype.unshift.call(args, this.id);
        if (console && console[logType]) {
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
        this.historyStorage.push(arguments);
    };

    /**
     * Returns the history for the logger.
     * @return {Array}
     */
    Logger.prototype.getHistory = function () {
        return this.historyStorage;
    };

    /**
     * Starts a timer you can use to track how long an operation takes.
     * @param {String} label Timer name.
     */
    Logger.prototype.time = function (label) {
        this.timeStorage[label] = now();
    };

    /**
     * Stops a timer that was previously started by calling Logger.prototype.time().
     * @param {String} label Timer name.
     */
    Logger.prototype.timeEnd = function (label) {
        if (!this.timeStorage[label]) {
            return null;
        }

        this._log('log', [label, now() - this.timeStorage[label], 'ms']);
        delete this.timeStorage[label];
    };

    Logger.prototype.destroy = function () {
        destroyLogger(this);
    }

    return {
        getLogger: function (id, mode) {
            var logger = new Logger(id, mode);
            loggers.push(logger);
            return logger;
        },
        destroyLogger: destroyLogger
    };
});
}).call(this, define || RequireJS.define);
