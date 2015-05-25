/**
 * Course import-related js.
 */
define(
    ["jquery", "underscore", "gettext", "moment", "jquery.cookie"],
    function($, _, gettext, moment) {

        "use strict";

        /********** Private properties ****************************************/

        var STATE = {
            'READY'      : 1,
            'IN_PROGRESS': 2,
            'SUCCESS'    : 3,
            'ERROR'      : 4
        }

        var current = { stage: 0, state: STATE.READY };
        var file = { name: null, url: null };
        var timeout = { id: null, delay: 1000 };
        var $dom = {
            stages: $('ol.status-progress').children(),
            successStage: $('.item-progresspoint-success'),
            wrapper: $('div.wrapper-status')
        };

        /********** Private functions *****************************************/

        /**
         * Destroys any event listener Import might have needed
         * during the process the import
         *
         */
        var destroyEventListeners = function () {
            window.onbeforeunload = null;
        }

        /**
         * Makes Import feedback status list visible
         *
         */
        var displayFeedbackList = function () {
            $dom.wrapper.removeClass('is-hidden');
        };

        /**
         * Initializes the event listeners
         *
         */
        var initEventListeners = function () {
            window.onbeforeunload = function () {
                if (current.stage <= 1 ) {
                    return gettext('Your import is in progress; navigating away will abort it.');
                }
            }
        }

        /**
         * Sets the Import on the "success" status
         * (callbacks: complete)
         *
         * If it wasn't already, marks the stored import as "completed",
         * and updates its date timestamp
         */
        var success = function () {
            current.state = STATE.SUCCESS;

            if (CourseImport.storedImport().completed !== true) {
                storeImport(true);
            }

            destroyEventListeners();
            updateFeedbackList();

            if (typeof CourseImport.callbacks.complete === 'function') {
                CourseImport.callbacks.complete();
            }
        };

        /**
         * Updates the Import feedback status list
         *
         * @param {string} [currStageMsg=''] The message to show on the
         *   current stage (for now only in case of error)
         */
        var updateFeedbackList = function (currStageMsg) {
            var $checkmark = $dom.successStage.find('.icon');
            currStageMsg = currStageMsg || '';

            function completeStage(stage) {
                $(stage)
                    .removeClass("is-not-started is-started")
                    .addClass("is-complete");
            }

            function resetStage(stage) {
                $(stage)
                    .removeClass("is-complete is-started has-error")
                    .addClass("is-not-started")
                    .find('p.error').remove().end()
                    .find('p.copy').show();
            }

            switch (current.state) {
                case STATE.READY:
                    _.map($dom.stages, resetStage);

                    break;

                case STATE.IN_PROGRESS:
                    var $prev = $dom.stages.slice(0, current.stage);
                    var $curr = $dom.stages.eq(current.stage);

                    _.map($prev, completeStage);
                    $curr.removeClass("is-not-started").addClass("is-started");

                    break;

                case STATE.SUCCESS:
                    var successUnix = CourseImport.storedImport().date;
                    var date = moment(successUnix).utc().format('MM/DD/YYYY');
                    var time = moment(successUnix).utc().format('HH:mm');

                    _.map($dom.stages, completeStage);

                    $dom.successStage
                        .find('.item-progresspoint-success-date')
                        .html('(' + date + ' at ' + time + ' UTC)');

                    break;

                case STATE.ERROR:
                    // Make all stages up to, and including, the error stage 'complete'.
                    var $prev = $dom.stages.slice(0, current.stage + 1);
                    var $curr = $dom.stages.eq(current.stage);
                    var $next = $dom.stages.slice(current.stage + 1);
                    var error = currStageMsg || gettext("There was an error with the upload");

                    _.map($prev, completeStage);
                    _.map($next, resetStage);

                    if (!$curr.hasClass('has-error')) {
                        $curr
                            .removeClass('is-started')
                            .addClass('has-error')
                            .find('p.copy')
                            .hide()
                            .after("<p class='copy error'>" + error + "</p>");
                    }

                    break;
            }

            if (current.state === STATE.SUCCESS) {
                $checkmark.removeClass('fa-square-o').addClass('fa-check-square-o');
            } else {
                $checkmark.removeClass('fa-check-square-o').addClass('fa-square-o');
            }
        };


        /**
         * Stores in a cookie the current import data
         *
         * @param {boolean} [completed=false] If the import has been completed or not
         */
        var storeImport = function (completed) {
            $.cookie('lastfileupload', JSON.stringify({
                file: file,
                date: moment().valueOf(),
                completed: completed || false
            }));
        }

        /********** Public functions ******************************************/

        var CourseImport = {

            /**
             * A collection of callbacks.
             * For now the only supported is 'complete', called on success/error
             *
             */
            callbacks: {},

            /**
             * Sets the Import in the "error" status.
             * (callbacks: complete)
             *
             * Immediately stops any further polling from the server.
             * Displays the error message at the list element that corresponds
             * to the stage where the error occurred.
             *
             * @param {string} msg Error message to display.
             * @param {int} [stage=current.stage] Stage of import process at which error occurred.
             */
            error: function (msg, stage) {
                current.stage = Math.abs(stage || current.stage); // Could be negative
                current.state = STATE.ERROR;

                destroyEventListeners();
                clearTimeout(timeout.id);
                updateFeedbackList(msg);

                if (typeof this.callbacks.complete === 'function') {
                    this.callbacks.complete();
                }
            },

            /**
             * Entry point for server feedback
             *
             * Checks for import status updates every `timeout` milliseconds,
             * and updates the page accordingly.
             *
             * @param {int} [stage=0] Starting stage.
             */
            pollStatus: function (stage) {
                var self = this;

                if (current.state !== STATE.IN_PROGRESS) {
                    return;
                }

                current.stage = stage || 0;

                if (current.stage === 4) { // Succeeded
                    success();
                } else if (current.stage < 0) { // Failed
                    this.error(gettext("Error importing course"));
                } else { // In progress
                    updateFeedbackList();

                    $.getJSON(file.url, function (data) {
                        timeout.id = setTimeout(function () {
                            self.pollStatus(data.ImportStatus);
                        }, timeout.delay);
                    });
                }
            },

            /**
             * Resets the Import internally and visually
             *
             */
            reset: function () {
                current.stage = 0;
                current.state = STATE.READY;

                updateFeedbackList();
            },

            /**
             * Show last import status from server and start sending requests
             * to the server for status updates
             *
             */
            resume: function () {
                var self = this;

                file = self.storedImport().file;

                $.getJSON(file.url, function (data) {
                    current.stage = data.ImportStatus;

                    if (current.stage !== 0) {
                        current.state = STATE.IN_PROGRESS;
                        displayFeedbackList();

                        self.pollStatus(current.stage);
                    }
                });
            },

            /**
             * Starts the importing process.
             * Makes status list visible and starts showing upload progress.
             *
             * @param {string} fileName The name of the file to import
             * @param {string} fileUrl The full URL to use to query the server
             *     about the import status
             */
            start: function (fileName, fileUrl) {
                current.state = STATE.IN_PROGRESS;

                file.name = fileName;
                file.url = fileUrl;

                initEventListeners();
                storeImport();
                displayFeedbackList();
                updateFeedbackList();
            },

            /**
             * Fetches the previous stored import
             *
             * @return {JSON} the data of the previous import
             */
            storedImport: function () {
                return JSON.parse($.cookie('lastfileupload'));
            }
        };

        return CourseImport;
    });
