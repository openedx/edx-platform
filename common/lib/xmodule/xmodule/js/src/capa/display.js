/* global MathJax, Collapsible, interpolate, JavascriptLoader, Logger, CodeMirror */
// Note: this code was originally converted from CoffeeScript, and thus follows some
// coding conventions that are discouraged by eslint. Some warnings have been suppressed
// to avoid substantial rewriting of the code. Allow the eslint suppressions to exceed
// the max line length of 120.
/* eslint max-len: ["error", 120, { "ignoreComments": true }] */

(function() {
    'use strict';
    var indexOfHelper = [].indexOf ||
        function(item) {
            var i, len;
            for (i = 0, len = this.length; i < len; i++) {
                if (i in this && this[i] === item) {
                    return i;
                }
            }
            return -1;
        };

    this.Problem = (function() {
        function Problem(element) {
            var that = this;
            this.hint_button = function() {
                return Problem.prototype.hint_button.apply(that, arguments);
            };
            this.enableSubmitButtonAfterTimeout = function() {
                return Problem.prototype.enableSubmitButtonAfterTimeout.apply(that, arguments);
            };
            this.enableSubmitButtonAfterResponse = function() {
                return Problem.prototype.enableSubmitButtonAfterResponse.apply(that, arguments);
            };
            this.enableSubmitButton = function(enable, changeText) {
                if (changeText === null || changeText === undefined) {
                    changeText = true; // eslint-disable-line no-param-reassign
                }
                return Problem.prototype.enableSubmitButton.apply(that, arguments);
            };
            this.enableAllButtons = function(enable, isFromCheckOperation) { // eslint-disable-line no-unused-vars
                return Problem.prototype.enableAllButtons.apply(that, arguments);
            };
            this.disableAllButtonsWhileRunning = function(
                operationCallback, isFromCheckOperation // eslint-disable-line no-unused-vars
            ) {
                return Problem.prototype.disableAllButtonsWhileRunning.apply(that, arguments);
            };
            this.submitAnswersAndSubmitButton = function(bind) {
                if (bind === null || bind === undefined) {
                    bind = false;  // eslint-disable-line no-param-reassign
                }
                return Problem.prototype.submitAnswersAndSubmitButton.apply(that, arguments);
            };
            this.refreshAnswers = function() {
                return Problem.prototype.refreshAnswers.apply(that, arguments);
            };
            this.updateMathML = function(jax, el) { // eslint-disable-line no-unused-vars
                return Problem.prototype.updateMathML.apply(that, arguments);
            };
            this.refreshMath = function(event, el) { // eslint-disable-line no-unused-vars
                return Problem.prototype.refreshMath.apply(that, arguments);
            };
            this.save_internal = function() {
                return Problem.prototype.save_internal.apply(that, arguments);
            };
            this.save = function() {
                return Problem.prototype.save.apply(that, arguments);
            };
            this.gentle_alert = function(msg) { // eslint-disable-line no-unused-vars
                return Problem.prototype.gentle_alert.apply(that, arguments);
            };
            this.clear_all_notifications = function() {
                return Problem.prototype.clear_all_notifications.apply(that, arguments);
            };
            this.show = function() {
                return Problem.prototype.show.apply(that, arguments);
            };
            this.reset_internal = function() {
                return Problem.prototype.reset_internal.apply(that, arguments);
            };
            this.reset = function() {
                return Problem.prototype.reset.apply(that, arguments);
            };
            this.get_sr_status = function(contents) { // eslint-disable-line no-unused-vars
                return Problem.prototype.get_sr_status.apply(that, arguments);
            };
            this.submit_internal = function() {
                return Problem.prototype.submit_internal.apply(that, arguments);
            };
            this.submit = function() {
                return Problem.prototype.submit.apply(that, arguments);
            };
            this.submit_fd = function() {
                return Problem.prototype.submit_fd.apply(that, arguments);
            };
            this.focus_on_save_notification = function() {
                return Problem.prototype.focus_on_save_notification.apply(that, arguments);
            };
            this.focus_on_hint_notification = function() {
                return Problem.prototype.focus_on_hint_notification.apply(that, arguments);
            };
            this.focus_on_submit_notification = function() {
                return Problem.prototype.focus_on_submit_notification.apply(that, arguments);
            };
            this.focus_on_notification = function(type) { // eslint-disable-line no-unused-vars
                return Problem.prototype.focus_on_notification.apply(that, arguments);
            };
            this.scroll_to_problem_meta = function() {
                return Problem.prototype.scroll_to_problem_meta.apply(that, arguments);
            };
            this.submit_save_waitfor = function(callback) { // eslint-disable-line no-unused-vars
                return Problem.prototype.submit_save_waitfor.apply(that, arguments);
            };
            this.setupInputTypes = function() {
                return Problem.prototype.setupInputTypes.apply(that, arguments);
            };
            this.poll = function(prevTimeout, focusCallback // eslint-disable-line no-unused-vars
            ) {
                return Problem.prototype.poll.apply(that, arguments);
            };
            this.queueing = function(focusCallback) { // eslint-disable-line no-unused-vars
                return Problem.prototype.queueing.apply(that, arguments);
            };
            this.forceUpdate = function(response) { // eslint-disable-line no-unused-vars
                return Problem.prototype.forceUpdate.apply(that, arguments);
            };
            this.updateProgress = function(response) { // eslint-disable-line no-unused-vars
                return Problem.prototype.updateProgress.apply(that, arguments);
            };
            this.renderProgressState = function() {
                return Problem.prototype.renderProgressState.apply(that, arguments);
            };
            this.bind = function() {
                return Problem.prototype.bind.apply(that, arguments);
            };
            this.el = $(element).find('.problems-wrapper');
            this.id = this.el.data('problem-id');
            this.element_id = this.el.attr('id');
            this.url = this.el.data('url');
            this.content = this.el.data('content');

            // has_timed_out and has_response are used to ensure that
            // we wait a minimum of ~ 1s before transitioning the submit
            // button from disabled to enabled
            this.has_timed_out = false;
            this.has_response = false;
            this.render(this.content);
        }

        Problem.prototype.$ = function(selector) {
            return $(selector, this.el);
        };

        Problem.prototype.bind = function() {
            var problemPrefix,
                that = this;
            if (typeof MathJax !== 'undefined' && MathJax !== null) {
                this.el.find('.problem > div').each(function(index, element) {
                    return MathJax.Hub.Queue(['Typeset', MathJax.Hub, element]);
                });
            }
            window.update_schematics();
            problemPrefix = this.element_id.replace(/problem_/, '');
            this.inputs = this.$('[id^="input_' + problemPrefix + '_"]');
            this.$('div.action button').click(this.refreshAnswers);
            this.reviewButton = this.$('.notification-btn.review-btn');
            this.reviewButton.click(this.scroll_to_problem_meta);
            this.submitButton = this.$('.action .submit');
            this.submitButtonLabel = this.$('.action .submit .submit-label');
            this.submitButtonSubmitText = this.submitButtonLabel.text();
            this.submitButtonSubmittingText = this.submitButton.data('submitting');
            this.submitButton.click(this.submit_fd);
            this.hintButton = this.$('.action .hint-button');
            this.hintButton.click(this.hint_button);
            this.resetButton = this.$('.action .reset');
            this.resetButton.click(this.reset);
            this.showButton = this.$('.action .show');
            this.showButton.click(this.show);
            this.saveButton = this.$('.action .save');
            this.saveNotification = this.$('.notification-save');
            this.saveButton.click(this.save);
            this.gentleAlertNotification = this.$('.notification-gentle-alert');
            this.submitNotification = this.$('.notification-submit');

            // Accessibility helper for sighted keyboard users to show <clarification> tooltips on focus:
            this.$('.clarification').focus(function(ev) {
                var icon;
                icon = $(ev.target).children('i');
                return window.globalTooltipManager.openTooltip(icon);
            });
            this.$('.clarification').blur(function() {
                return window.globalTooltipManager.hide();
            });
            this.$('.review-btn').focus(function(ev) {
                return $(ev.target).removeClass('sr');
            });
            this.$('.review-btn').blur(function(ev) {
                return $(ev.target).addClass('sr');
            });
            this.bindResetCorrectness();
            if (this.submitButton.length) {
                this.submitAnswersAndSubmitButton(true);
            }
            Collapsible.setCollapsibles(this.el);
            this.$('input.math').keyup(this.refreshMath);
            if (typeof MathJax !== 'undefined' && MathJax !== null) {
                this.$('input.math').each(function(index, element) {
                    return MathJax.Hub.Queue([that.refreshMath, null, element]);
                });
            }
        };

        Problem.prototype.renderProgressState = function() {
            var graded, progress, progressTemplate, curScore, totalScore, attemptsUsed;
            curScore = this.el.data('problem-score');
            totalScore = this.el.data('problem-total-possible');
            attemptsUsed = this.el.data('attempts-used');
            graded = this.el.data('graded');

            if (curScore === undefined || totalScore === undefined) {
                progress = '';
            } else if (attemptsUsed === 0 || totalScore === 0) {
                // Render 'x point(s) possible' if student has not yet attempted question
                if (graded === 'True' && totalScore !== 0) {
                    progressTemplate = ngettext(
                        // Translators: %(num_points)s is the number of points possible (examples: 1, 3, 10).;
                        '%(num_points)s point possible (graded)', '%(num_points)s points possible (graded)',
                        totalScore
                    );
                } else {
                    progressTemplate = ngettext(
                        // Translators: %(num_points)s is the number of points possible (examples: 1, 3, 10).;
                        '%(num_points)s point possible (ungraded)', '%(num_points)s points possible (ungraded)',
                        totalScore
                    );
                }
                progress = interpolate(progressTemplate, {num_points: totalScore}, true);
            } else {
                // Render 'x/y point(s)' if student has attempted question
                if (graded === 'True' && totalScore !== 0) {
                    progressTemplate = ngettext(
                        // This comment needs to be on one line to be properly scraped for the translators.
                        // Translators: %(earned)s is the number of points earned. %(possible)s is the total number of points (examples: 0/1, 1/1, 2/3, 5/10). The total number of points will always be at least 1. We pluralize based on the total number of points (example: 0/1 point; 1/2 points);
                        '%(earned)s/%(possible)s point (graded)', '%(earned)s/%(possible)s points (graded)',
                        totalScore
                    );
                } else {
                    progressTemplate = ngettext(
                        // This comment needs to be on one line to be properly scraped for the translators.
                        // Translators: %(earned)s is the number of points earned. %(possible)s is the total number of points (examples: 0/1, 1/1, 2/3, 5/10). The total number of points will always be at least 1. We pluralize based on the total number of points (example: 0/1 point; 1/2 points);
                        '%(earned)s/%(possible)s point (ungraded)', '%(earned)s/%(possible)s points (ungraded)',
                        totalScore
                    );
                }
                progress = interpolate(
                    progressTemplate, {
                        earned: curScore,
                        possible: totalScore
                    }, true
                );
            }
            return this.$('.problem-progress').text(progress);
        };

        Problem.prototype.updateProgress = function(response) {
            if (response.progress_changed) {
                this.el.data('problem-score', response.current_score);
                this.el.data('problem-total-possible', response.total_possible);
                this.el.data('attempts-used', response.attempts_used);
                this.el.trigger('progressChanged');
            }
            return this.renderProgressState();
        };

        Problem.prototype.forceUpdate = function(response) {
            this.el.data('problem-score', response.current_score);
            this.el.data('problem-total-possible', response.total_possible);
            this.el.data('attempts-used', response.attempts_used);
            this.el.trigger('progressChanged');
            return this.renderProgressState();
        };

        Problem.prototype.queueing = function(focusCallback) {
            var that = this;
            this.queued_items = this.$('.xqueue');
            this.num_queued_items = this.queued_items.length;
            if (this.num_queued_items > 0) {
                if (window.queuePollerID) { // Only one poller 'thread' per Problem
                    window.clearTimeout(window.queuePollerID);
                }
                window.queuePollerID = window.setTimeout(function() {
                    return that.poll(1000, focusCallback);
                }, 1000);
            }
        };

        Problem.prototype.poll = function(previousTimeout, focusCallback) {
            var that = this;
            return $.postWithPrefix('' + this.url + '/problem_get', function(response) {
                var newTimeout;
                // If queueing status changed, then render
                that.new_queued_items = $(response.html).find('.xqueue');
                if (that.new_queued_items.length !== that.num_queued_items) {
                    edx.HtmlUtils.setHtml(that.el, edx.HtmlUtils.HTML(response.html)).promise().done(function() {
                        return typeof focusCallback === 'function' ? focusCallback() : void 0;
                    });
                    JavascriptLoader.executeModuleScripts(that.el, function() {
                        that.setupInputTypes();
                        that.bind();
                    });
                }
                that.num_queued_items = that.new_queued_items.length;
                if (that.num_queued_items === 0) {
                    that.forceUpdate(response);
                    delete window.queuePollerID;
                } else {
                    newTimeout = previousTimeout * 2;
                    // if the timeout is greather than 1 minute
                    if (newTimeout >= 60000) {
                        delete window.queuePollerID;
                        that.gentle_alert(
                            gettext('The grading process is still running. Refresh the page to see updates.')
                        );
                    } else {
                        window.queuePollerID = window.setTimeout(function() {
                            return that.poll(newTimeout, focusCallback);
                        }, newTimeout);
                    }
                }
            });
        };

        /**
         * Use this if you want to make an ajax call on the input type object
         * static method so you don't have to instantiate a Problem in order to use it
         *
         * Input:
         *     url: the AJAX url of the problem
         *     inputId: the inputId of the input you would like to make the call on
         *         NOTE: the id is the ${id} part of "input_${id}" during rendering
         *             If this function is passed the entire prefixed id, the backend may have trouble
         *             finding the correct input
         *     dispatch: string that indicates how this data should be handled by the inputtype
         *     data: dictionary of data to send to the server
         *     callback: the function that will be called once the AJAX call has been completed.
         *          It will be passed a response object
         */
        Problem.inputAjax = function(url, inputId, dispatch, data, callback) {
            data.dispatch = dispatch; // eslint-disable-line no-param-reassign
            data.input_id = inputId; // eslint-disable-line no-param-reassign
            return $.postWithPrefix('' + url + '/input_ajax', data, callback);
        };

        Problem.prototype.render = function(content, focusCallback) {
            var that = this;
            if (content) {
                this.el.html(content);
                return JavascriptLoader.executeModuleScripts(this.el, function() {
                    that.setupInputTypes();
                    that.bind();
                    that.queueing(focusCallback);
                    that.renderProgressState();
                    return typeof focusCallback === 'function' ? focusCallback() : void 0;
                });
            } else {
                return $.postWithPrefix('' + this.url + '/problem_get', function(response) {
                    that.el.html(response.html);
                    return JavascriptLoader.executeModuleScripts(that.el, function() {
                        that.setupInputTypes();
                        that.bind();
                        that.queueing();
                        return that.forceUpdate(response);
                    });
                });
            }
        };

        Problem.prototype.setupInputTypes = function() {
            var that = this;
            this.inputtypeDisplays = {};
            return this.el.find('.capa_inputtype').each(function(index, inputtype) {
                var classes, cls, id, setupMethod, i, len, results;
                classes = $(inputtype).attr('class').split(' ');
                id = $(inputtype).attr('id');
                results = [];
                for (i = 0, len = classes.length; i < len; i++) {
                    cls = classes[i];
                    setupMethod = that.inputtypeSetupMethods[cls];
                    if (setupMethod != null) {
                        results.push(that.inputtypeDisplays[id] = setupMethod(inputtype));
                    } else {
                        results.push(void 0);
                    }
                }
                return results;
            });
        };

        /**
         * If some function wants to be called before sending the answer to the
         * server, give it a chance to do so.
         *
         * submit_save_waitfor allows the callee to send alerts if the user's input is
         * invalid. To do so, the callee must throw an exception named "WaitforException".
         * This and any other errors or exceptions that arise from the callee are rethrown
         * and abort the submission.
         *
         * In order to use this feature, add a 'data-waitfor' attribute to the input,
         * and specify the function to be called by the submit button before sending off @answers
         */
        Problem.prototype.submit_save_waitfor = function(callback) {
            var flag, inp, i, len, ref,
                that = this;
            flag = false;
            ref = this.inputs;
            for (i = 0, len = ref.length; i < len; i++) {
                inp = ref[i];
                if ($(inp).is('input[waitfor]')) {
                    try {
                        $(inp).data('waitfor')(function() {
                            that.refreshAnswers();
                            return callback();
                        });
                    } catch (e) {
                        if (e.name === 'Waitfor Exception') {
                            alert(e.message); // eslint-disable-line no-alert
                        } else {
                            alert( // eslint-disable-line no-alert
                                gettext('Could not grade your answer. The submission was aborted.')
                            );
                        }
                        throw e;
                    }
                    flag = true;
                } else {
                    flag = false;
                }
            }
            return flag;
        };

        // Scroll to problem metadata and next focus is problem input
        Problem.prototype.scroll_to_problem_meta = function() {
            var questionTitle;
            questionTitle = this.$('.problem-header');
            if (questionTitle.length > 0) {
                $('html, body').animate({
                    scrollTop: questionTitle.offset().top
                }, 500);
                questionTitle.focus();
            }
        };

        Problem.prototype.focus_on_notification = function(type) {
            var notification;
            notification = this.$('.notification-' + type);
            if (notification.length > 0) {
                notification.focus();
            }
        };

        Problem.prototype.focus_on_submit_notification = function() {
            this.focus_on_notification('submit');
        };

        Problem.prototype.focus_on_hint_notification = function() {
            this.focus_on_notification('hint');
        };

        Problem.prototype.focus_on_save_notification = function() {
            this.focus_on_notification('save');
        };

        /**
         * 'submit_fd' uses FormData to allow file submissions in the 'problem_check' dispatch,
         *      in addition to simple querystring-based answers
         *
         * NOTE: The dispatch 'problem_check' is being singled out for the use of FormData;
         *       maybe preferable to consolidate all dispatches to use FormData
         */
        Problem.prototype.submit_fd = function() {
            var abortSubmission, error, errorHtml, errors, fd, fileNotSelected, fileTooLarge, maxFileSize,
                requiredFilesNotSubmitted, settings, timeoutId, unallowedFileSubmitted, i, len,
                that = this;

            // If there are no file inputs in the problem, we can fall back on submit.
            if (this.el.find('input:file').length === 0) {
                this.submit();
                return;
            }
            this.enableSubmitButton(false);
            if (!window.FormData) {
                alert(gettext('Submission aborted! Sorry, your browser does not support file uploads. If you can, please use Chrome or Safari which have been verified to support file uploads.')); // eslint-disable-line max-len, no-alert
                this.enableSubmitButton(true);
                return;
            }
            timeoutId = this.enableSubmitButtonAfterTimeout();
            fd = new FormData();

            // Sanity checks on submission
            maxFileSize = 4 * 1000 * 1000;
            fileTooLarge = false;
            fileNotSelected = false;
            requiredFilesNotSubmitted = false;
            unallowedFileSubmitted = false;

            errors = [];
            this.inputs.each(function(index, element) {
                var allowedFiles, file, maxSize, requiredFiles, loopI, loopLen, ref;
                if (element.type === 'file') {
                    requiredFiles = $(element).data('required_files');
                    allowedFiles = $(element).data('allowed_files');
                    ref = element.files;
                    for (loopI = 0, loopLen = ref.length; loopI < loopLen; loopI++) {
                        file = ref[loopI];
                        if (allowedFiles.length !== 0 && indexOfHelper.call(allowedFiles, file.name < 0)) {
                            unallowedFileSubmitted = true;
                            errors.push(edx.StringUtils.interpolate(
                                gettext('You submitted {filename}; only {allowedFiles} are allowed.'), {
                                    filename: file.name,
                                    allowedFiles: allowedFiles
                                }
                            ));
                        }
                        if (indexOfHelper.call(requiredFiles, file.name) >= 0) {
                            requiredFiles.splice(requiredFiles.indexOf(file.name), 1);
                        }
                        if (file.size > maxFileSize) {
                            fileTooLarge = true;
                            maxSize = maxFileSize / (1000 * 1000);
                            errors.push(edx.StringUtils.interpolate(
                                gettext('Your file {filename} is too large (max size: {maxSize}MB).'), {
                                    filename: file.name,
                                    maxSize: maxSize
                                }
                            ));
                        }
                        fd.append(element.id, file);
                    }
                    if (element.files.length === 0) {
                        fileNotSelected = true;
                        fd.append(element.id, ''); // In case we want to allow submissions with no file
                    }
                    if (requiredFiles.length !== 0) {
                        requiredFilesNotSubmitted = true;
                        errors.push(edx.StringUtils.interpolate(
                            gettext('You did not submit the required files: {requiredFiles}.'), {
                                requiredFiles: requiredFiles
                            }
                        ));
                    }
                } else {
                    fd.append(element.id, element.value);
                }
            });
            if (fileNotSelected) {
                errors.push(gettext('You did not select any files to submit.'));
            }
            errorHtml = '<ul>\n';
            for (i = 0, len = errors.length; i < len; i++) {
                error = errors[i];
                errorHtml += '<li>' + error + '</li>\n';
            }
            errorHtml += '</ul>';
            this.gentle_alert(errorHtml);
            abortSubmission = fileTooLarge || fileNotSelected || unallowedFileSubmitted || requiredFilesNotSubmitted;
            if (abortSubmission) {
                window.clearTimeout(timeoutId);
                this.enableSubmitButton(true);
            } else {
                settings = {
                    type: 'POST',
                    data: fd,
                    processData: false,
                    contentType: false,
                    complete: this.enableSubmitButtonAfterResponse,
                    success: function(response) {
                        switch (response.success) {
                        case 'incorrect':
                        case 'correct':
                            that.render(response.contents);
                            that.updateProgress(response);
                            break;
                        default:
                            that.gentle_alert(response.success);
                        }
                        return Logger.log('problem_graded', [that.answers, response.contents], that.id);
                    }
                };
                $.ajaxWithPrefix('' + this.url + '/problem_check', settings);
            }
        };

        Problem.prototype.submit = function() {
            if (!this.submit_save_waitfor(this.submit_internal)) {
                this.disableAllButtonsWhileRunning(this.submit_internal, true);
            }
        };

        Problem.prototype.submit_internal = function() {
            var that = this;
            Logger.log('problem_check', this.answers);
            return $.postWithPrefix('' + this.url + '/problem_check', this.answers, function(response) {
                switch (response.success) {
                case 'incorrect':
                case 'correct':
                    window.SR.readTexts(that.get_sr_status(response.contents));
                    that.el.trigger('contentChanged', [that.id, response.contents, response]);
                    that.render(response.contents, that.focus_on_submit_notification);
                    that.updateProgress(response);
                    break;
                default:
                    that.saveNotification.hide();
                    that.gentle_alert(response.success);
                }
                return Logger.log('problem_graded', [that.answers, response.contents], that.id);
            });
        };

        /**
         * This method builds up an array of strings to send to the page screen-reader span.
         * It first gets all elements with class "status", and then looks to see if they are contained
         * in sections with aria-labels. If so, labels are prepended to the status element text.
         * If not, just the text of the status elements are returned.
         */
        Problem.prototype.get_sr_status = function(contents) {
            var addedStatus, ariaLabel, element, labeledStatus, parentSection, statusElement, template, i, len;
            statusElement = $(contents).find('.status');
            labeledStatus = [];
            for (i = 0, len = statusElement.length; i < len; i++) {
                element = statusElement[i];
                parentSection = $(element).closest('.wrapper-problem-response');
                addedStatus = false;
                if (parentSection) {
                    ariaLabel = parentSection.attr('aria-label');
                    if (ariaLabel) {
                        // Translators: This is only translated to allow for reordering of label and associated status.;
                        template = gettext('{label}: {status}');
                        labeledStatus.push(edx.StringUtils.interpolate(
                            template, {
                                label: ariaLabel,
                                status: $(element).text()
                            }
                        ));
                        addedStatus = true;
                    }
                }
                if (!addedStatus) {
                    labeledStatus.push($(element).text());
                }
            }
            return labeledStatus;
        };

        Problem.prototype.reset = function() {
            return this.disableAllButtonsWhileRunning(this.reset_internal, false);
        };

        Problem.prototype.reset_internal = function() {
            var that = this;
            Logger.log('problem_reset', this.answers);
            return $.postWithPrefix('' + this.url + '/problem_reset', {
                id: this.id
            }, function(response) {
                if (response.success) {
                    that.el.trigger('contentChanged', [that.id, response.html, response]);
                    that.render(response.html, that.scroll_to_problem_meta);
                    that.updateProgress(response);
                    return window.SR.readText(gettext('This problem has been reset.'));
                } else {
                    return that.gentle_alert(response.msg);
                }
            });
        };

        // TODO this needs modification to deal with javascript responses; perhaps we
        // need something where responsetypes can define their own behavior when show
        // is called.
        Problem.prototype.show = function() {
            var that = this;
            Logger.log('problem_show', {
                problem: this.id
            });
            return $.postWithPrefix('' + this.url + '/problem_show', function(response) {
                var answers;
                answers = response.answers;
                $.each(answers, function(key, value) {
                    var answer, choice, i, len, results;
                    if ($.isArray(value)) {
                        results = [];
                        for (i = 0, len = value.length; i < len; i++) {
                            choice = value[i];
                            results.push(that.$('label[for="input_' + key + '_' + choice + '"]').attr({
                                correct_answer: 'true'
                            }));
                        }
                        return results;
                    } else {
                        answer = that.$('#answer_' + key + ', #solution_' + key);
                        edx.HtmlUtils.setHtml(answer, edx.HtmlUtils.HTML(value));
                        Collapsible.setCollapsibles(answer);

                        // Sometimes, `value` is just a string containing a MathJax formula.
                        // If this is the case, jQuery will throw an error in some corner cases
                        // because of an incorrect selector. We setup a try..catch so that
                        // the script doesn't break in such cases.
                        //
                        // We will fallback to the second `if statement` below, if an
                        // error is thrown by jQuery.
                        try {
                            return $(value).find('.detailed-solution');
                        } catch (e) {
                            return {};
                        }

                        // TODO remove the above once everything is extracted into its own
                        // inputtype functions.
                    }
                });
                that.el.find('.capa_inputtype').each(function(index, inputtype) {
                    var classes, cls, display, showMethod, i, len, results;
                    classes = $(inputtype).attr('class').split(' ');
                    results = [];
                    for (i = 0, len = classes.length; i < len; i++) {
                        cls = classes[i];
                        display = that.inputtypeDisplays[$(inputtype).attr('id')];
                        showMethod = that.inputtypeShowAnswerMethods[cls];
                        if (showMethod != null) {
                            results.push(showMethod(inputtype, display, answers));
                        } else {
                            results.push(void 0);
                        }
                    }
                    return results;
                });
                if (typeof MathJax !== 'undefined' && MathJax !== null) {
                    that.el.find('.problem > div').each(function(index, element) {
                        return MathJax.Hub.Queue(['Typeset', MathJax.Hub, element]);
                    });
                }
                that.el.find('.show').attr('disabled', 'disabled');
                that.updateProgress(response);
                window.SR.readText(gettext('Answers to this problem are now shown. Navigate through the problem to review it with answers inline.')); // eslint-disable-line max-len
                that.scroll_to_problem_meta();
            });
        };

        Problem.prototype.clear_all_notifications = function() {
            this.submitNotification.remove();
            this.gentleAlertNotification.hide();
            this.saveNotification.hide();
        };

        Problem.prototype.gentle_alert = function(msg) {
            edx.HtmlUtils.setHtml(
                this.el.find('.notification-gentle-alert .notification-message'),
                edx.HtmlUtils.HTML(msg)
            );
            this.clear_all_notifications();
            this.gentleAlertNotification.show();
            this.gentleAlertNotification.focus();
        };

        Problem.prototype.save = function() {
            if (!this.submit_save_waitfor(this.save_internal)) {
                this.disableAllButtonsWhileRunning(this.save_internal, false);
            }
        };

        Problem.prototype.save_internal = function() {
            var that = this;
            Logger.log('problem_save', this.answers);
            return $.postWithPrefix('' + this.url + '/problem_save', this.answers, function(response) {
                var saveMessage;
                saveMessage = response.msg;
                if (response.success) {
                    that.el.trigger('contentChanged', [that.id, response.html, response]);
                    edx.HtmlUtils.setHtml(
                        that.el.find('.notification-save .notification-message'),
                        edx.HtmlUtils.HTML(saveMessage)
                    );
                    that.clear_all_notifications();
                    that.el.find('.wrapper-problem-response .message').hide();
                    that.saveNotification.show();
                    that.focus_on_save_notification();
                } else {
                    that.gentle_alert(saveMessage);
                }
            });
        };

        Problem.prototype.refreshMath = function(event, element) {
            var elid, eqn, jax, mathjaxPreprocessor, preprocessorTag, target;
            if (!element) {
                element = event.target; // eslint-disable-line no-param-reassign
            }
            elid = element.id.replace(/^input_/, '');
            target = 'display_' + elid;

            // MathJax preprocessor is loaded by 'setupInputTypes'
            preprocessorTag = 'inputtype_' + elid;
            mathjaxPreprocessor = this.inputtypeDisplays[preprocessorTag];
            if (typeof MathJax !== 'undefined' && MathJax !== null && MathJax.Hub.getAllJax(target)[0]) {
                jax = MathJax.Hub.getAllJax(target)[0];
                eqn = $(element).val();
                if (mathjaxPreprocessor) {
                    eqn = mathjaxPreprocessor(eqn);
                }
                MathJax.Hub.Queue(['Text', jax, eqn], [this.updateMathML, jax, element]);
            }
        };

        Problem.prototype.updateMathML = function(jax, element) {
            try {
                $('#' + element.id + '_dynamath').val(jax.root.toMathML(''));
            } catch (exception) {
                if (!exception.restart) {
                    throw exception;
                }
                if (typeof MathJax !== 'undefined' && MathJax !== null) {
                    MathJax.Callback.After([this.refreshMath, jax], exception.restart);
                }
            }
        };

        Problem.prototype.refreshAnswers = function() {
            this.$('input.schematic').each(function(index, element) {
                return element.schematic.update_value();
            });
            this.$('.CodeMirror').each(function(index, element) {
                if (element.CodeMirror.save) {
                    element.CodeMirror.save();
                }
            });
            this.answers = this.inputs.serialize();
        };

        /**
         * Used to check available answers and if something is checked (or the answer is set in some textbox),
         * the "Submit" button becomes enabled. Otherwise it is disabled by default.
         *
         * Arguments:
         *    bind (boolean): used on the first check to attach event handlers to input fields
         *       to change "Submit" enable status in case of some manipulations with answers
         */
        Problem.prototype.submitAnswersAndSubmitButton = function(bind) {
            var answered, atLeastOneTextInputFound, oneTextInputFilled,
                that = this;
            if (bind === null || bind === undefined) {
                bind = false; // eslint-disable-line no-param-reassign
            }
            answered = true;
            atLeastOneTextInputFound = false;
            oneTextInputFilled = false;
            this.el.find('input:text').each(function(i, textField) {
                if ($(textField).is(':visible')) {
                    atLeastOneTextInputFound = true;
                    if ($(textField).val() !== '') {
                        oneTextInputFilled = true;
                    }
                    if (bind) {
                        $(textField).on('input', function() {
                            that.saveNotification.hide();
                            that.submitAnswersAndSubmitButton();
                        });
                    }
                }
            });
            if (atLeastOneTextInputFound && !oneTextInputFilled) {
                answered = false;
            }
            this.el.find('.choicegroup').each(function(i, choicegroupBlock) {
                var checked;
                checked = false;
                $(choicegroupBlock).find('input[type=checkbox], input[type=radio]').
                    each(function(j, checkboxOrRadio) {
                        if ($(checkboxOrRadio).is(':checked')) {
                            checked = true;
                        }
                        if (bind) {
                            $(checkboxOrRadio).on('click', function() {
                                that.saveNotification.hide();
                                that.submitAnswersAndSubmitButton();
                            });
                        }
                    });
                if (!checked) {
                    answered = false;
                }
            });
            this.el.find('select').each(function(i, selectField) {
                var selectedOption = $(selectField).find('option:selected').text()
                    .trim();
                if (selectedOption === 'Select an option') {
                    answered = false;
                }
                if (bind) {
                    $(selectField).on('change', function() {
                        that.saveNotification.hide();
                        that.submitAnswersAndSubmitButton();
                    });
                }
            });
            if (answered) {
                return this.enableSubmitButton(true);
            } else {
                return this.enableSubmitButton(false, false);
            }
        };

        Problem.prototype.bindResetCorrectness = function() {
            // Loop through all input types.
            // Bind the reset functions at that scope.
            var $inputtypes,
                that = this;
            $inputtypes = this.el.find('.capa_inputtype').add(this.el.find('.inputtype'));
            return $inputtypes.each(function(index, inputtype) {
                var bindMethod, classes, cls, i, len, results;
                classes = $(inputtype).attr('class').split(' ');
                results = [];
                for (i = 0, len = classes.length; i < len; i++) {
                    cls = classes[i];
                    bindMethod = that.bindResetCorrectnessByInputtype[cls];
                    if (bindMethod != null) {
                        results.push(bindMethod(inputtype));
                    } else {
                        results.push(void 0);
                    }
                }
                return results;
            });
        };

        // Find all places where each input type displays its correct-ness
        // Replace them with their original state--'unanswered'.
        Problem.prototype.bindResetCorrectnessByInputtype = {
            // These are run at the scope of the capa inputtype
            // They should set handlers on each <input> to reset the whole.
            formulaequationinput: function(element) {
                return $(element).find('input').on('input', function() {
                    var $p;
                    $p = $(element).find('span.status');
                    return $p.parent().removeAttr('class').addClass('unsubmitted');
                });
            },
            choicegroup: function(element) {
                var $element, id;
                $element = $(element);
                id = ($element.attr('id').match(/^inputtype_(.*)$/))[1];
                return $element.find('input').on('change', function() {
                    var $status;
                    $status = $('#status_' + id);
                    if ($status[0]) {
                        $status.removeAttr('class').addClass('unanswered');
                    } else {
                        $('<span>', {
                            class: 'unanswered',
                            style: 'display: inline-block;',
                            id: 'status_' + id
                        });
                    }
                    return $element.find('label').removeAttr('class');
                });
            },
            'option-input': function(element) {
                var $select, id;
                $select = $(element).find('select');
                id = ($select.attr('id').match(/^input_(.*)$/))[1];
                return $select.on('change', function() {
                    return $('#status_' + id).removeAttr('class').addClass('unanswered')
                        .find('.sr')
                        .text(gettext('unsubmitted'));
                });
            },
            textline: function(element) {
                return $(element).find('input').on('input', function() {
                    var $p;
                    $p = $(element).find('span.status');
                    return $p.parent().removeClass('correct incorrect').addClass('unsubmitted');
                });
            }
        };

        Problem.prototype.inputtypeSetupMethods = {
            'text-input-dynamath': function(element) {
                /*
                 Return: function (eqn) -> eqn that preprocesses the user formula input before
                 it is fed into MathJax. Return 'false' if no preprocessor specified
                 */
                var data, preprocessor, preprocessorClass, preprocessorClassName;
                data = $(element).find('.text-input-dynamath_data');
                preprocessorClassName = data.data('preprocessor');
                preprocessorClass = window[preprocessorClassName];
                if (preprocessorClass == null) {
                    return false;
                } else {
                    preprocessor = new preprocessorClass();
                    return preprocessor.fn;
                }
            },
            cminput: function(container) {
                var CodeMirrorEditor, CodeMirrorTextArea, element, id, linenumbers, mode, spaces, tabsize;
                element = $(container).find('textarea');
                tabsize = element.data('tabsize');
                mode = element.data('mode');
                linenumbers = element.data('linenums');
                spaces = Array(parseInt(tabsize, 10) + 1).join(' ');
                CodeMirrorEditor = CodeMirror.fromTextArea(element[0], {
                    lineNumbers: linenumbers,
                    indentUnit: tabsize,
                    tabSize: tabsize,
                    mode: mode,
                    matchBrackets: true,
                    lineWrapping: true,
                    indentWithTabs: false,
                    smartIndent: false,
                    extraKeys: {
                        Esc: function() {
                            $('.grader-status').focus();
                            return false;
                        },
                        Tab: function(cm) {
                            cm.replaceSelection(spaces, 'end');
                            return false;
                        }
                    }
                });
                id = element.attr('id').replace(/^input_/, '');
                CodeMirrorTextArea = CodeMirrorEditor.getInputField();
                CodeMirrorTextArea.setAttribute('id', 'cm-textarea-' + id);
                CodeMirrorTextArea.setAttribute('aria-describedby', 'cm-editor-exit-message-' + id + ' status_' + id);
                return CodeMirrorEditor;
            }
        };

        Problem.prototype.inputtypeShowAnswerMethods = {
            choicegroup: function(element, display, answers) {
                var answer, choice, inputId, i, len, results, $element;
                $element = $(element);
                inputId = $element.attr('id').replace(/inputtype_/, '');
                answer = answers[inputId];
                results = [];
                for (i = 0, len = answer.length; i < len; i++) {
                    choice = answer[i];
                    results.push($element.find('#input_' + inputId + '_' + choice).parent('label').
                        addClass('choicegroup_correct'));
                }
                return results;
            },
            choicetextgroup: function(element, display, answers) {
                var answer, choice, inputId, i, len, results, $element;
                $element = $(element);
                inputId = $element.attr('id').replace(/inputtype_/, '');
                answer = answers[inputId];
                results = [];
                for (i = 0, len = answer.length; i < len; i++) {
                    choice = answer[i];
                    results.push($element.find('section#forinput' + choice).addClass('choicetextgroup_show_correct'));
                }
                return results;
            },
            imageinput: function(element, display, answers) {
                // answers is a dict of (answer_id, answer_text) for each answer for this question.
                //
                // @Examples:
                // {'anwser_id': {
                //    'rectangle': '(10,10)-(20,30);(12,12)-(40,60)',
                //    'regions': '[[10,10], [30,30], [10, 30], [30, 10]]'
                // } }
                var canvas, container, id, types, context, $element;
                types = {
                    rectangle: function(ctx, coords) {
                        var rects, reg;
                        reg = /^\(([0-9]+),([0-9]+)\)-\(([0-9]+),([0-9]+)\)$/;
                        rects = coords.replace(/\s*/g, '').split(/;/);
                        $.each(rects, function(index, rect) {
                            var abs, height, points, width;
                            abs = Math.abs;
                            points = reg.exec(rect);
                            if (points) {
                                width = abs(points[3] - points[1]);
                                height = abs(points[4] - points[2]);
                                ctx.rect(points[1], points[2], width, height);
                            }
                        });
                        ctx.stroke();
                        return ctx.fill();
                    },
                    regions: function(ctx, coords) {
                        var parseCoords;
                        parseCoords = function(coordinates) {
                            var reg;
                            reg = JSON.parse(coordinates);

                            // Regions is list of lists [region1, region2, region3, ...] where regionN
                            // is disordered list of points: [[1,1], [100,100], [50,50], [20, 70]].
                            // If there is only one region in the list, simpler notation can be used:
                            // regions="[[10,10], [30,30], [10, 30], [30, 10]]" (without explicitly
                            // setting outer list)
                            if (typeof reg[0][0][0] === 'undefined') {
                                // we have [[1,2],[3,4],[5,6]] - single region
                                // instead of [[[1,2],[3,4],[5,6], [[1,2],[3,4],[5,6]]]
                                // or [[[1,2],[3,4],[5,6]]] - multiple regions syntax
                                reg = [reg];
                            }
                            return reg;
                        };
                        return $.each(parseCoords(coords), function(index, region) {
                            ctx.beginPath();
                            $.each(region, function(idx, point) {
                                if (idx === 0) {
                                    return ctx.moveTo(point[0], point[1]);
                                } else {
                                    return ctx.lineTo(point[0], point[1]);
                                }
                            });
                            ctx.closePath();
                            ctx.stroke();
                            return ctx.fill();
                        });
                    }
                };
                $element = $(element);
                id = $element.attr('id').replace(/inputtype_/, '');
                container = $element.find('#answer_' + id);
                canvas = document.createElement('canvas');
                canvas.width = container.data('width');
                canvas.height = container.data('height');
                if (canvas.getContext) {
                    context = canvas.getContext('2d');
                } else {
                    console.log('Canvas is not supported.'); // eslint-disable-line no-console
                }
                context.fillStyle = 'rgba(255,255,255,.3)';
                context.strokeStyle = '#FF0000';
                context.lineWidth = '2';
                if (answers[id]) {
                    $.each(answers[id], function(key, value) {
                        if ((types[key] !== null && types[key] !== undefined) && value) {
                            types[key](context, value);
                        }
                    });
                    container.html(canvas);
                } else {
                    console.log('Answer is absent for image input with id=' + id); // eslint-disable-line no-console
                }
            }
        };

        /**
         * Used to keep the buttons disabled while operationCallback is running.
         *
         * params:
         *      'operationCallback' is an operation to be run.
         *      isFromCheckOperation' is a boolean to keep track if 'operationCallback' was
         *           from submit, if so then text of submit button will be changed as well.
         *
         */
        Problem.prototype.disableAllButtonsWhileRunning = function(operationCallback, isFromCheckOperation) {
            var that = this;
            this.enableAllButtons(false, isFromCheckOperation);
            return operationCallback().always(function() {
                return that.enableAllButtons(true, isFromCheckOperation);
            });
        };

        /**
         * Used to enable/disable all buttons in problem.
         *
         * params:
         *     'enable' is a boolean to determine enabling/disabling of buttons.
         *     'isFromCheckOperation' is a boolean to keep track if operation was initiated
         *         from submit so that text of submit button will also be changed while disabling/enabling
         *         the submit button.
         */
        Problem.prototype.enableAllButtons = function(enable, isFromCheckOperation) {
            // Called by disableAllButtonsWhileRunning to automatically disable all buttons while check,reset, or
            // save internal are running. Then enable all the buttons again after it is done.
            if (enable) {
                this.resetButton.add(this.saveButton).add(this.hintButton).add(this.showButton).
                    removeAttr('disabled');
            } else {
                this.resetButton.add(this.saveButton).add(this.hintButton).add(this.showButton).
                    attr({disabled: 'disabled'});
            }
            return this.enableSubmitButton(enable, isFromCheckOperation);
        };

        /**
         *  Used to disable submit button to reduce chance of accidental double-submissions.
         *
         * params:
         *     'enable' is a boolean to determine enabling/disabling of submit button.
         *     'changeText' is a boolean to determine if there is need to change the
         *         text of submit button as well.
         */
        Problem.prototype.enableSubmitButton = function(enable, changeText) {
            var submitCanBeEnabled;
            if (changeText === null || changeText === undefined) {
                changeText = true; // eslint-disable-line no-param-reassign
            }
            if (enable) {
                submitCanBeEnabled = this.submitButton.data('should-enable-submit-button') === 'True';
                if (submitCanBeEnabled) {
                    this.submitButton.removeAttr('disabled');
                }
                if (changeText) {
                    this.submitButtonLabel.text(this.submitButtonSubmitText);
                }
            } else {
                this.submitButton.attr({disabled: 'disabled'});
                if (changeText) {
                    this.submitButtonLabel.text(this.submitButtonSubmittingText);
                }
            }
        };

        Problem.prototype.enableSubmitButtonAfterResponse = function() {
            this.has_response = true;
            if (!this.has_timed_out) {
                // Server has returned response before our timeout.
                return this.enableSubmitButton(false);
            } else {
                return this.enableSubmitButton(true);
            }
        };

        Problem.prototype.enableSubmitButtonAfterTimeout = function() {
            var enableSubmitButton,
                that = this;
            this.has_timed_out = false;
            this.has_response = false;
            enableSubmitButton = function() {
                that.has_timed_out = true;
                if (that.has_response) {
                    that.enableSubmitButton(true);
                }
            };
            return window.setTimeout(enableSubmitButton, 750);
        };

        Problem.prototype.hint_button = function() {
            // Store the index of the currently shown hint as an attribute.
            // Use that to compute the next hint number when the button is clicked.
            var hintContainer, hintIndex, nextIndex,
                that = this;
            hintContainer = this.$('.problem-hint');
            hintIndex = hintContainer.attr('hint_index');
            if (hintIndex === void 0) {
                nextIndex = 0;
            } else {
                nextIndex = parseInt(hintIndex, 10) + 1;
            }
            return $.postWithPrefix('' + this.url + '/hint_button', {
                hint_index: nextIndex,
                input_id: this.id
            }, function(response) {
                var hintMsgContainer;
                if (response.success) {
                    hintMsgContainer = that.$('.problem-hint .notification-message');
                    hintContainer.attr('hint_index', response.hint_index);
                    edx.HtmlUtils.setHtml(hintMsgContainer, edx.HtmlUtils.HTML(response.msg));
                    MathJax.Hub.Queue(['Typeset', MathJax.Hub, hintContainer[0]]);
                    if (response.should_enable_next_hint) {
                        that.hintButton.removeAttr('disabled');
                    } else {
                        that.hintButton.attr({disabled: 'disabled'});
                    }
                    that.el.find('.notification-hint').show();
                    that.focus_on_hint_notification();
                } else {
                    that.gentle_alert(response.msg);
                }
            });
        };

        return Problem;
    }).call(this);
}).call(this);
