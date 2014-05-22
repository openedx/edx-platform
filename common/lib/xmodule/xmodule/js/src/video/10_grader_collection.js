(function (define) {
'use strict';
define(
'video/10_grader_collection.js',
['video/00_abstract_grader.js'],
function (AbstractGrader) {
    /**
     * GraderCollection module.
     * @exports video/10_grader_collection.js
     * @constructor
     * @param {Object} state The object containing the state of the video
     * player.
     * @return {jquery Promise}
     */
    var GraderCollection = function (element, state) {
        if (!(this instanceof GraderCollection)) {
            return new GraderCollection(element, state);
        }

        var hasScore = state.config.hasScore,
            graders = state.config.graders,
            conversions = {
                'basic_grader': 'BasicGrader',
                'scored_on_end': 'GradeOnEnd',
                'scored_on_percent': 'GradeOnPercent'
            };

        return (!hasScore) ? [] : $.map(graders, function (config, name) {
            var graderName = conversions[name],
                Grader = GraderCollection[graderName];

            if (Grader && !config.isScored) {
                return new Grader(element, state, config);
            }
        });
    };

    /** Write graders below this line **/

    GraderCollection.BasicGrader = AbstractGrader.extend({
        name: 'basic_grader',

        getGrader: function (element) {
            var downloadButton =  this.state.el.find('.video-download-button');

            this.dfd = $.Deferred();
            element.on('play', this.dfd.resolve);
            downloadButton.on('click', this.onDownloadHandler.bind(this));

            return this.dfd.promise();
        },

        onDownloadHandler: function () {
            // We have to wait for a some time, otherwise browser might cancel
            // the request.
            setTimeout(this.dfd.resolve, 25);
        }
    });

    GraderCollection.GradeOnEnd = AbstractGrader.extend({
        name: 'scored_on_end',

        getGrader: function (element) {
            var downloadButton =  this.state.el.find('.video-download-button');

            this.dfd = $.Deferred();
            element.on('play', _.once(this.onPlayHandler.bind(this)));
            downloadButton.on('click', this.onDownloadHandler.bind(this));

            return this.dfd.promise();
        },

        onDownloadHandler: function () {
            // We have to wait for a some time, otherwise browser might cancel
            // the request.
            setTimeout(this.dfd.resolve, 25);
        },

        onPlayHandler: function (event, time) {
            setTimeout(function () {
                var range = this.getStartEndTimes(),
                    size = range.size,
                    duration = range.duration,
                    eventName = (size === duration) ? 'ended' : 'endTime';

                this.element
                    .on(eventName, this.dfd.resolve)
                    .on('seek', this.onSeekHandler.bind(this));
            }.bind(this), 0);
        },

        onSeekHandler: function (event, time) {
            setTimeout(function () {
                var range = this.getStartEndTimes();

                if (Math.floor(time) === range.end) {
                    this.dfd.resolve();
                }
            }.bind(this), 0);
        }
    });

    GraderCollection.GradeOnPercent = AbstractGrader.extend({
        name: 'scored_on_percent',
        size: 100,

        getGrader: function (element, state, config) {
            this.dfd = $.Deferred();
            this.coef = 1;
            this.graderValue = this.config.graderValue + 1;

            if (this.config.graderValue === 0) {
                this.dfd.resolve();
            } else {
                element.on('play', _.once(this.onPlayHandler.bind(this)));
            }

            return this.dfd.promise();
        },

        getProgress: function (timeline) {
            return _.compact(timeline).length * this.coef;
        },

        createTimeline: function () {
            return [];
        },

        getStoredLocally: function () {
            var cumulative = this.storage.getItem('cumulative_score', true),
                value = null;

            try {
                value = JSON.parse(cumulative)[this.getName()];
            } catch (ex) { }

            return value;
        },

        getTimeline: function (size) {
            var current = this.timeline,
                storedOnServer = this.config.graderState,
                storedLocally = this.getStoredLocally(),
                timeline = current || storedLocally || storedOnServer || [];

            if (!size) {
                size = this.size;
            }

            return timeline.length && size === this.size ?
                timeline :
                this.createTimeline();
        },

        onPlayHandler: function (event) {
            setTimeout(function () {
                var interval, waitTime;

                this.range = this.getStartEndTimes();
                interval = 1000 * this.range.size;
                // event `progress` triggers with interval 200 ms.
                waitTime = Math.max(interval/this.size, 200);

                // We're going to receive 1-2 events `progress` for each
                // timeline position for the small videos to be more precise and
                // to avoid some issues with invoking of timers.
                if (waitTime <= 1000) {
                    this.size = interval / 1000;
                    this.coef = 100 / this.size;
                }

                this.timeline = this.getTimeline(this.size);

                this.element.on(
                    'progress',
                    _.throttle(
                        this.onProgressHandler.bind(this), waitTime,
                        { leading: true, trailing: true }
                    )
                );
            }.bind(this), 0);
        },

        onProgressHandler: function (event, time) {
            var seconds = Math.floor(time);

            if (this.range.start <= seconds && seconds <= this.range.end) {
                var position = Math.floor(
                    (time - this.range.start) * this.size / this.range.size
                );

                if (!this.timeline[position]) {
                    this.timeline[position] = 1;
                    if (this.getProgress(this.timeline) >= this.graderValue) {
                        this.dfd.resolve();
                    }
                }
            }
        },

        getState: function () {
            return this.getTimeline();
        }
    });

    return GraderCollection;
});

}(window.RequireJS.define));
