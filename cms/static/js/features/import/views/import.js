/**
 * Course import-related js.
 */
define(
    ['jquery', 'underscore', 'gettext', 'moment', 'edx-ui-toolkit/js/utils/html-utils', 'jquery.cookie'],
    function($, _, gettext, moment, HtmlUtils) {
        'use strict';

        /** ******** Private properties ****************************************/

        var COOKIE_NAME = 'lastimportupload';

        var STAGE = {
            UPLOADING: 0,
            UNPACKING: 1,
            VERIFYING: 2,
            UPDATING: 3,
            SUCCESS: 4
        };

        var STATE = {
            READY: 1,
            IN_PROGRESS: 2,
            SUCCESS: 3,
            ERROR: 4
        };

        var current = {stage: 0, state: STATE.READY};
        var deferred = null;
        var file = {name: null, url: null};
        var timeout = {id: null, delay: 3000};
        var $dom = {
            stages: $('ol.status-progress').children(),
            successStage: $('.item-progresspoint-success'),
            wrapper: $('div.wrapper-status')
        };

        var CourseImport;

        /** ******** Private functions *****************************************/

        /**
         * Destroys any event listener Import might have needed
         * during the process the import
         *
         */
        var destroyEventListeners = function() {
            $(window).off('beforeunload.import');
        };

        /**
         * Makes Import feedback status list visible
         *
         */
        var displayFeedbackList = function() {
            $dom.wrapper.removeClass('is-hidden');
        };

        /**
         * Initializes the event listeners
         *
         */
        var initEventListeners = function() {
            $(window).on('beforeunload.import', function() {  // eslint-disable-line consistent-return
                if (current.stage < STAGE.UNPACKING) {
                    return gettext('Your import is in progress; navigating away will abort it.');
                }
            });
        };

        /**
         * Stores in a cookie the current import data
         *
         * @param {boolean} [completed=false] If the import has been completed or not
         */
        var storeImport = function(completed) {
            $.cookie(COOKIE_NAME, JSON.stringify({
                file: file,
                date: moment().valueOf(),
                completed: completed || false
            }), {path: window.location.pathname});
        };

        /**
         * Updates the Import feedback status list
         *
         * @param {string} [currStageMsg=''] The message to show on the
         *   current stage (for now only in case of error)
         */
        var updateFeedbackList = function(currStageMsg) {
            var $checkmark, $curr, $prev, $next;
            var date, stageMsg, successUnix, time;

            $checkmark = $dom.successStage.find('.icon');
            stageMsg = currStageMsg || '';

            function completeStage(stage) {
                $(stage)
                    .removeClass('is-not-started is-started')
                    .addClass('is-complete');
            }

            function errorStage(stage) {
                if (!$(stage).hasClass('has-error')) {
                    stageMsg = HtmlUtils.joinHtml(
                        HtmlUtils.HTML('<p class="copy error">'),
                        stageMsg,
                        HtmlUtils.HTML('</p>')
                    );
                    $(stage)
                        .removeClass('is-started')
                        .addClass('has-error')
                        .find('p.copy')
                        .hide()
                        .after(HtmlUtils.ensureHtml(stageMsg).toString());
                }
            }

            function resetStage(stage) {
                $(stage)
                    .removeClass('is-complete is-started has-error')
                    .addClass('is-not-started')
                    .find('p.error')
                    .remove()
                    .end()
                    .find('p.copy')
                    .show();
            }

            switch (current.state) {
            case STATE.READY:
                _.map($dom.stages, resetStage);

                break;

            case STATE.IN_PROGRESS:
                $prev = $dom.stages.slice(0, current.stage);
                $curr = $dom.stages.eq(current.stage);

                _.map($prev, completeStage);
                $curr.removeClass('is-not-started').addClass('is-started');

                break;

            case STATE.SUCCESS:
                successUnix = CourseImport.storedImport().date;
                date = moment(successUnix).utc().format('MM/DD/YYYY');
                time = moment(successUnix).utc().format('HH:mm');

                _.map($dom.stages, completeStage);

                $dom.successStage
                        .find('.item-progresspoint-success-date')
                        .text('(' + date + ' at ' + time + ' UTC)');

                break;

            case STATE.ERROR:
                    // Make all stages up to, and including, the error stage 'complete'.
                $prev = $dom.stages.slice(0, current.stage + 1);
                $curr = $dom.stages.eq(current.stage);
                $next = $dom.stages.slice(current.stage + 1);

                _.map($prev, completeStage);
                _.map($next, resetStage);
                errorStage($curr);

                break;

            default:
                break;
            }

            if (current.state === STATE.SUCCESS) {
                $checkmark.removeClass('fa-square-o').addClass('fa-check-square-o');
            } else {
                $checkmark.removeClass('fa-check-square-o').addClass('fa-square-o');
            }
        };

        /**
         * Sets the Import in the "error" status.
         *
         * Immediately stops any further polling from the server.
         * Displays the error message at the list element that corresponds
         * to the stage where the error occurred.
         *
         * @param {string} msg Error message to display.
         * @param {int} [stage=current.stage] Stage of import process at which error occurred.
         */
        var error = function(msg, stage) {
            current.stage = Math.abs(stage || current.stage); // Could be negative
            current.state = STATE.ERROR;

            destroyEventListeners();
            clearTimeout(timeout.id);
            updateFeedbackList(msg);

            deferred.resolve();
        };

        /**
         * Sets the Import on the "success" status
         *
         * If it wasn't already, marks the stored import as "completed",
         * and updates its date timestamp
         */
        var success = function() {
            current.state = STATE.SUCCESS;

            if (CourseImport.storedImport().completed !== true) {
                storeImport(true);
            }

            destroyEventListeners();
            updateFeedbackList();

            deferred.resolve();
        };

        /** ******** Public functions ******************************************/

        CourseImport = {

            /**
             * Cancels the import and sets the Object to the error state
             *
             * @param {string} msg Error message to display.
             * @param {int} stage Stage of import process at which error occurred.
             */
            cancel: function(msg, stage) {
                error(msg, stage);
            },

            /**
             * Entry point for server feedback
             *
             * Checks for import status updates every `timeout` milliseconds,
             * and updates the page accordingly.
             *
             * @param {int} [stage=0] Starting stage.
             */
            pollStatus: function(stage, message) {
                if (current.state !== STATE.IN_PROGRESS) {
                    return;
                }

                current.stage = stage || STAGE.UPLOADING;

                if (current.stage === STAGE.SUCCESS) {
                    success();
                } else if (current.stage < STAGE.UPLOADING) { // Failed
                    error(message || gettext('Error importing course'));
                } else { // In progress
                    updateFeedbackList();

                    $.getJSON(file.url, function(data) {
                        timeout.id = setTimeout(function() {
                            this.pollStatus(data.ImportStatus, data.Message);
                        }.bind(this), timeout.delay);
                    }.bind(this));
                }
            },

            /**
             * Resets the Import internally and visually
             *
             */
            reset: function() {
                current.stage = STAGE.UPLOADING;
                current.state = STATE.READY;

                clearTimeout(timeout.id);
                updateFeedbackList();
            },

            /**
             * Show last import status from server and start sending requests
             * to the server for status updates
             *
             * @return {jQuery promise}
             */
            resume: function() {
                deferred = $.Deferred();
                file = this.storedImport().file;

                $.getJSON(file.url, function(data) {
                    current.stage = data.ImportStatus;

                    displayFeedbackList();

                    if (current.stage !== STAGE.UPLOADING) {
                        current.state = STATE.IN_PROGRESS;

                        this.pollStatus(current.stage, data.Message);
                    } else {
                        // An import in the upload stage cannot be resumed
                        error(gettext('There was an error with the upload'));
                    }
                }.bind(this));

                return deferred.promise();
            },

            /**
             * Starts the importing process.
             * Makes status list visible and starts showing upload progress.
             *
             * @param {string} fileName The name of the file to import
             * @param {string} fileUrl The full URL to use to query the server
             *     about the import status
             * @return {jQuery promise}
             */
            start: function(fileName, fileUrl) {
                current.state = STATE.IN_PROGRESS;
                deferred = $.Deferred();

                file.name = fileName;
                file.url = fileUrl;

                initEventListeners();
                storeImport();
                displayFeedbackList();
                updateFeedbackList();

                return deferred.promise();
            },

            /**
             * Fetches the previous stored import
             *
             * @return {JSON} the data of the previous import
             */
            storedImport: function() {
                return JSON.parse($.cookie(COOKIE_NAME));
            }
        };

        return CourseImport;
    });
