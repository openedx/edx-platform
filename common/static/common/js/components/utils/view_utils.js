/**
 * Provides useful utilities for views.
 */
(function(define, require) {
    'use strict';

    /* RequireJS */
    define(['jquery', 'underscore', 'gettext', 'common/js/components/views/feedback_notification',
        'common/js/components/views/feedback_prompt', 'edx-ui-toolkit/js/utils/html-utils'],
    function($, _, gettext, NotificationView, PromptView, HtmlUtils) {
    /* End RequireJS */
    /* Webpack
    define(['jquery', 'underscore', 'gettext', 'common/js/components/views/feedback_notification',
        'common/js/components/views/feedback_prompt', 'scriptjs'],
        function($, _, gettext, NotificationView, PromptView, $script) {
    /* End Webpack */

        var toggleExpandCollapse, showLoadingIndicator, hideLoadingIndicator, confirmThenRunOperation,
            runOperationShowingMessage, showErrorMeassage, withDisabledElement, disableElementWhileRunning,
            getScrollOffset, setScrollOffset, setScrollTop, redirect, reload, hasChangedAttributes,
            deleteNotificationHandler, validateRequiredField, validateURLItemEncoding,
            validateTotalKeyLength, checkTotalKeyLengthViolations, loadJavaScript;

        // see https://openedx.atlassian.net/browse/TNL-889 for what is it and why it's 65
        var MAX_SUM_KEY_LENGTH = 65;

        /**
             * Toggles the expanded state of the current element.
             */
        toggleExpandCollapse = function(target, collapsedClass) {
            // Support the old 'collapsed' option until fully switched over to is-collapsed
            var collapsed = collapsedClass || 'collapsed';
            target.closest('.expand-collapse').toggleClass('expand collapse');
            target.closest('.is-collapsible, .window').toggleClass(collapsed);
            target.closest('.is-collapsible').children('article').slideToggle();
        };

        /**
             * Show the page's loading indicator.
             */
        showLoadingIndicator = function() {
            $('.ui-loading').show();
        };

        /**
             * Hide the page's loading indicator.
             */
        hideLoadingIndicator = function() {
            $('.ui-loading').hide();
        };

        /**
             * Confirms with the user whether to run an operation or not, and then runs it if desired.
             */
        confirmThenRunOperation = function(title, message, actionLabel, operation, onCancelCallback) {
            return new PromptView.Warning({
                title: title,
                message: message,
                actions: {
                    primary: {
                        text: actionLabel,
                        click: function(prompt) {
                            prompt.hide();
                            operation();
                        }
                    },
                    secondary: {
                        text: gettext('Cancel'),
                        click: function(prompt) {
                            if (onCancelCallback) {
                                onCancelCallback();
                            }
                            return prompt.hide();
                        }
                    }
                }
            }).show();
        };

        /**
             * Shows a progress message for the duration of an asynchronous operation.
             * Note: this does not remove the notification upon failure because an error
             * will be shown that shouldn't be removed.
             * @param message The message to show.
             * @param operation A function that returns a promise representing the operation.
             */
        runOperationShowingMessage = function(message, operation) {
            var notificationView;
            notificationView = new NotificationView.Mini({
                title: gettext(message)
            });
            notificationView.show();
            return operation().done(function() {
                notificationView.hide();
            });
        };

        /**
             * Shows an error notification message for a specifc period of time.
             * @param heading The heading of notification.
             * @param message The message to show.
             * @param timeInterval The time interval to hide the notification.
             */
        showErrorMeassage = function(heading, message, timeInterval) {
            var errorNotificationView = new NotificationView.Error({
                title: gettext(heading),
                message: gettext(message)
            });
            errorNotificationView.show();

            setTimeout(function() { errorNotificationView.hide(); }, timeInterval);
        };
        /**
             * Wraps a Backbone event callback to disable the event's target element.
             *
             * This paradigm is designed to be used in Backbone event maps where
             * multiple events firing simultaneously is not desired.
             *
             * @param functionName the function to execute, as a string.
             * The function must return a jQuery promise and be able to take an event
             */
        withDisabledElement = function(functionName) {
            return function(event) {
                var view = this;
                disableElementWhileRunning($(event.currentTarget), function() {
                    // call view.functionName(event), with view as the current this
                    return view[functionName].apply(view, [event]);
                });
            };
        };

        /**
             * Disables a given element when a given operation is running.
             * @param {jQuery} element the element to be disabled.
             * @param operation the operation during whose duration the
             * element should be disabled. The operation should return
             * a JQuery promise.
             */
        disableElementWhileRunning = function(element, operation) {
            element.addClass('is-disabled').attr('aria-disabled', true);
            return operation().always(function() {
                element.removeClass('is-disabled').attr('aria-disabled', false);
            });
        };

        /**
             * Returns a handler that removes a notification, both dismissing it and deleting it from the database.
             * @param callback function to call when deletion succeeds
             */
        deleteNotificationHandler = function(callback) {
            return function(event) {
                event.preventDefault();
                $.ajax({
                    url: $(this).data('dismiss-link'),
                    type: 'DELETE',
                    success: callback
                });
            };
        };

        /**
             * Performs an animated scroll so that the window has the specified scroll top.
             * @param scrollTop The desired scroll top for the window.
             */
        setScrollTop = function(scrollTop) {
            $('html, body').animate({
                scrollTop: scrollTop
            }, 500);
        };

        /**
             * Returns the relative position that the element is scrolled from the top of the view port.
             * @param element The element in question.
             */
        getScrollOffset = function(element) {
            var elementTop = element.offset().top;
            return elementTop - $(window).scrollTop();
        };

        /**
             * Scrolls the window so that the element is scrolled down to the specified relative position
             * from the top of the view port.
             * @param element The element in question.
             * @param offset The amount by which the element should be scrolled from the top of the view port.
             */
        setScrollOffset = function(element, offset) {
            var elementTop = element.offset().top,
                newScrollTop = elementTop - offset;
            setScrollTop(newScrollTop);
        };

        /**
             * Redirects to the specified URL. This is broken out as its own function for unit testing.
             */
        redirect = function(url) {
            window.location = url;
        };

        /**
             * Reloads the page. This is broken out as its own function for unit testing.
             */
        reload = function() {
            window.location.reload();
        };

        /**
             * Returns true if a model has changes to at least one of the specified attributes.
             * @param model The model in question.
             * @param attributes The list of attributes to be compared.
             * @returns {boolean} Returns true if attribute changes are found.
             */
        hasChangedAttributes = function(model, attributes) {
            var i,
                changedAttributes = model.changedAttributes();
            if (!changedAttributes) {
                return false;
            }
            for (i = 0; i < attributes.length; i++) {
                if (_.has(changedAttributes, attributes[i])) {
                    return true;
                }
            }
            return false;
        };

        /**
             * Helper method for course/library creation - verifies a required field is not blank.
             */
        validateRequiredField = function(msg) {
            return msg.length === 0 ? gettext('Required field.') : '';
        };

        /**
             * Helper method for course/library creation.
             * Check that a course (org, number, run) doesn't use any special characters
             */
        validateURLItemEncoding = function(item, allowUnicode) {
            var required = validateRequiredField(item);
            if (required) {
                return required;
            }
            if (allowUnicode) {
                if (/\s/g.test(item)) {
                    return gettext('Please do not use any spaces in this field.');
                }
            } else {
                if (item !== encodeURIComponent(item) || item.match(/[!'()*]/)) {
                    return gettext('Please do not use any spaces or special characters in this field.');
                }
            }
            return '';
        };

        // Ensure that sum length of key field values <= ${MAX_SUM_KEY_LENGTH} chars.
        validateTotalKeyLength = function(keyFieldSelectors) {
            var totalLength = _.reduce(
                keyFieldSelectors,
                function(sum, ele) { return sum + $(ele).val().length; },
                0
            );
            return totalLength <= MAX_SUM_KEY_LENGTH;
        };

        checkTotalKeyLengthViolations = function(selectors, classes, keyFieldSelectors, messageTpl) {
            var tempHtml;
            if (!validateTotalKeyLength(keyFieldSelectors)) {
                $(selectors.errorWrapper).addClass(classes.shown).removeClass(classes.hiding);
                tempHtml = HtmlUtils.joinHtml(
                    HtmlUtils.HTML('<p>'),
                    HtmlUtils.template(messageTpl)({limit: MAX_SUM_KEY_LENGTH}),
                    HtmlUtils.HTML('</p>')
                );
                HtmlUtils.setHtml(
                    $(selectors.errorMessage),
                    tempHtml
                );
                $(selectors.save).addClass(classes.disabled);
            } else {
                $(selectors.errorWrapper).removeClass(classes.shown).addClass(classes.hiding);
            }
        };

        /**
             * Dynamically loads the specified JavaScript file.
             * @param url The URL to a JavaScript file.
             * @returns {Promise} A promise indicating when the URL has been loaded.
             */
        loadJavaScript = function(url) {
            var deferred = $.Deferred();
            /* RequireJS */
            require([url],
                function() {
                    deferred.resolve();
                },
                function() {
                    deferred.reject();
                });
            /* End RequireJS */
            /* Webpack
                $script(url, url, function () {
                    deferred.resolve();
                });
                /* End Webpack */
            return deferred.promise();
        };

        return {
            toggleExpandCollapse: toggleExpandCollapse,
            showLoadingIndicator: showLoadingIndicator,
            hideLoadingIndicator: hideLoadingIndicator,
            confirmThenRunOperation: confirmThenRunOperation,
            runOperationShowingMessage: runOperationShowingMessage,
            showErrorMeassage: showErrorMeassage,
            withDisabledElement: withDisabledElement,
            disableElementWhileRunning: disableElementWhileRunning,
            deleteNotificationHandler: deleteNotificationHandler,
            setScrollTop: setScrollTop,
            getScrollOffset: getScrollOffset,
            setScrollOffset: setScrollOffset,
            redirect: redirect,
            reload: reload,
            hasChangedAttributes: hasChangedAttributes,
            validateRequiredField: validateRequiredField,
            validateURLItemEncoding: validateURLItemEncoding,
            validateTotalKeyLength: validateTotalKeyLength,
            checkTotalKeyLengthViolations: checkTotalKeyLengthViolations,
            loadJavaScript: loadJavaScript
        };
    });
}).call(this, define || RequireJS.define, require || RequireJS.require);
