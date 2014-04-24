(function (define) {
'use strict';
define(
'video/11_grader.js',
['video/10_grader_collection.js'],
function(GraderCollection) {
    /**
     * Grader module.
     * @exports video/11_grader.js
     * @constructor
     * @param {Object} state The object containing the state of the video
     * player.
     * @param {Object} i18n Object with translations.
     * @return {jquery Promise}
     */
    var Grader = function (state, i18n) {
        if (!(this instanceof Grader)) {
            return new Grader(state, i18n);
        }

        this.state = state;
        this.state.videoGrader = this;
        this.initialize(state, i18n);

        return $.Deferred().resolve().promise();
    };

    Grader.prototype = {
        gradersForSave: [],

        /** Initializes the module. */
        initialize: function (state, i18n) {
            this.state = state;
            this.i18n = i18n;
            this.el = this.state.el;
            this.maxScore = this.state.config.maxScore;
            this.score = this.state.config.score;
            this.url = this.state.config.gradeUrl;
            this.progressElement = this.state.progressElement;
            this.statusElement = this.state.statusElement;
            this.statusMsgElement = this.statusElement
                                        .find('.problem-feedback-message');

            if (this.score && isFinite(this.score)) {
                this.setScore(this.score);
                this.updateStatusText(
                    this.i18n['You\'ve received credit for viewing this video.']
                );
            } else {
                this.graders = this.getGraders(this.el, this.state);
                $.when.apply(this, this.getPromises(this.graders))
                    .done(this.onSuccess.bind(this))
                    .fail(this.onError.bind(this));
            }
        },

        /**
         * Factory method that returns instance of needed Grader.
         * @return {jquery Promise}
         * @example:
         *   var dfd = $.Deferred();
         *   this.el.on('play', dfd.resolve);
         *   return dfd.promise();
         */
        getGraders: function (element, state) {
            return new GraderCollection(element, state);
        },

        /**
         * Returns list of grader promises.
         * @return {Array} List of promises.
         */
        getPromises: function (graders) {
            return $.map(graders, function (grader) {
                return grader.getPromise();
            });
        },

        /**
         * Updates scores on the front-end.
         * @param {Number|String} points Score achieved by the student.
         * @param {Number|String} totalPoints Maximum number of points
         * achievable.
         */
        updateScores: function (points, totalPoints) {
            var msg = interpolate(
                    this.i18n['(%(points)s / %(total_points)s points)'],
                    {
                        'points': Number(points).toFixed(1),
                        'total_points': Number(totalPoints).toFixed(1)
                    }, true
                );

            this.progressElement.text(msg);
        },

        /**
         * Creates status element and inserts it to the DOM.
         * @param {String} message Status message.
         */
        createStatusElement: function (message) {
            this.statusElement = $([
                '<div class="problem-feedback video-feedback">',
                    message ? message : '',
                '</div>'
            ].join(''));

            this.statusMsgElement = this.statusElement
                                        .find('.problem-feedback-message');
            this.el.after(this.statusElement);
        },

        /**
         * Updates status message by the text passed as argument.
         * @param {String} text Text of status message.
         * @param {String} type The type of the message: error or success.
         */
        updateStatusText: function (text, type) {
            if (text) {
                if (this.statusElement.length) {
                    this.statusMsgElement.text(text);
                } else {
                    this.createStatusElement(text);
                }

                if (type === 'error') {
                    this.statusElement.addClass('is-error');
                } else {
                    this.statusElement.removeClass('is-error');
                }
            }
        },

        /**
         * Updates current score for the module.
         * @param {Number|String} points Score achieved by the student.
         */
        setScore: function (points) {
            this.score = points;
            this.state.storage.setItem('score', this.score, true);
            this.updateScores(this.score, this.maxScore);
        },

        /**
         * Handles success response from the server after sending grade results.
         * @param {Object} response Data returned from the server.
         * @param {String} textStatus String describing the status.
         * @param {jquery XHR} jqXHR
         */
        onSuccess: function (response) {
            if (isFinite(response)) {
                this.setScore(response);
                this.el.addClass('is-scored');
                this.updateStatusText(
                    this.i18n['You\'ve received credit for viewing this video.']
                );
            }
        },

        /**
         * Handles failed response from the server after sending grade results.
         * @param {jquery XHR} jqXHR
         * @param {String} textStatus String describing the type of error that
         * occurred and an optional exception object, if one occurred.
         * @param {String} errorThrown Textual portion of the HTTP status.
         */
        onError: function () {
            var msg = this.i18n.GRADER_ERROR;

            this.updateStatusText(msg, 'error');
            this.el.addClass('is-error');
        },

        getStates: function () {
            var states = {};

            if (this.graders.length) {
                if (!this.gradersForSave.length) {
                    this.gradersForSave = this.graders.filter(function (grader) {
                        return grader.config.saveState;
                    });
                }

                $.each(this.gradersForSave, function(index, grader) {
                    states[grader.getName()] = grader.getState();
                });
            }

            return states;
        }
    };

    return Grader;
});
}(RequireJS.define));
