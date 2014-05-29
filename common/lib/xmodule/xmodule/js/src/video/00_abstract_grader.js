(function (define) {
'use strict';
define(
'video/00_abstract_grader.js',
[],
function() {
    /**
     * Creates a new object with the specified prototype object and properties.
     * @param {Object} o The object which should be the prototype of the
     * newly-created object.
     * @private
     * @throws {TypeError, Error}
     * @return {Object}
     */
    var inherit = Object.create || (function () {
        var F = function () {};

        return function (o) {
            if (arguments.length > 1) {
                throw Error('Second argument not supported');
            }
            if (_.isNull(o) || _.isUndefined(o)) {
                throw Error('Cannot set a null [[Prototype]]');
            }
            if (!_.isObject(o)) {
                throw TypeError('Argument must be an object');
            }

            F.prototype = o;

            return new F();
        };
    })();

    /**
     * AbstractGrader module.
     * @exports video/00_abstract_grader.js
     * @constructor
     * @param {Object} state The object containing the state of the video
     * player.
     * @return {jquery Promise}
     */
    var AbstractGrader = function () {
        return this.initialize.apply(this, arguments);
    };

    /**
     * Returns new constructor that inherits form the current constructor.
     * @static
     * @param {Object} protoProps The object containing which will be added to
     * the prototype.
     * @return {Object}
     */
    AbstractGrader.extend = function (protoProps) {
        var Parent = this,
            Child = function () {
                if ($.isFunction(this.initialize)) {
                    return this.initialize.apply(this, arguments);
                }
            };

        // Inherit methods and properties from the Parent prototype.
        Child.prototype = inherit(Parent.prototype);
        Child.constructor = Parent;
        // Provide access to parent's methods and properties
        Child.__super__ = Parent.prototype;

        // Extends inherited methods and properties by methods/properties
        // passed as argument.
        if (protoProps) {
            $.extend(Child.prototype, protoProps);
        }

        return Child;
    };

    AbstractGrader.prototype = {
        /** Grader name on backend */
        name: '',
        range: {},

        /** Initializes the module. */
        initialize: function (element, state, config) {
            this.element = element;
            this.state = state;
            this.config = config;
            this.storage = this.state.storage;
            this.url = this.state.config.gradeUrl;
            this.grader = this.getGrader(this.element, this.state, this.config);
            this.promise = this.sendGradeOnSuccess(this.grader);
        },

        /** Returns grader name. */
        getName: function () {
            return this.name;
        },

        /**
         * Factory method that returns instance of needed Grader.
         * @return {jquery Promise}
         * @example:
         *   var dfd = $.Deferred();
         *   this.element.on('play', dfd.resolve);
         *   return dfd.promise();
         */
        getGrader: function (element, state, config) {
            throw new Error('Please implement logic of the `getGrader` method.');
        },

        /**
         * Sends results of grading to the server.
         * @return {jquery Promise}
         */
        sendGrade: function () {
            return $.ajaxWithPrefix({
                url: this.url,
                data: {
                    'graderName': this.getName()
                },
                type: 'POST',
                notifyOnError: false
            });
        },

        /**
         * Returns promise for the grader.
         * @return {jquery Promise}
         */
        getPromise: function () {
            return this.promise;
        },

        /**
         * Decorates provided grader so that it sends grade results on
         * successful scoring.
         * @param {jquery Promise} grader Grader function.
         */
        sendGradeOnSuccess: function (grader) {
            return grader.pipe(this.sendGrade.bind(this));
        },

        /**
         * Returns current grader progress object.
         * @return {Object} The object with key equals grader name and
         * value equals current state of the grader.
         */
        getState: function () {
            return null;
        },

        /**
         * Returns start/end times for the video.
         * @return {Object} Contains start, end times and size of the interval.
         */
        getStartEndTimes: function () {
            var startTime = this.state.config.startTime,
                endTime = this.state.config.endTime,
                duration = this.state.videoPlayer.duration();

            if (this.range && duration === this.range.duration) {
                return this.range;
            }

            if (startTime >= duration) {
                startTime = 0;
            }

            if (endTime <= startTime || endTime >= duration) {
                endTime = duration;
            }

            if (this.state.isFlashMode()) {
                startTime /= Number(this.state.speed);
                endTime /= Number(this.state.speed);
            }

            this.range = {
                start: startTime,
                end: endTime,
                size: endTime - startTime,
                duration: duration
            };

            return this.range;
        }
    };

    return AbstractGrader;
});
}(RequireJS.define));
