/**
 * Provides utilities for validating courses during creation, for both new courses and reruns.
 */
define(["jquery", "underscore", "gettext", "js/views/utils/view_utils"],
    function ($, _, gettext, ViewUtils) {
        "use strict";
        return function (selectors, classes) {
            var toggleSaveButton, validateTotalKeyLength, setFieldInErr,
                hasInvalidRequiredFields, create, validateFilledFields, configureHandlers;

            var validateRequiredField = ViewUtils.validateRequiredField;
            var validateURLItemEncoding = ViewUtils.validateURLItemEncoding;

            var keyLengthViolationMessage = gettext("The combined length of the organization, course number, and course run fields cannot be more than <%=limit%> characters.");

            var keyFieldSelectors = [selectors.org, selectors.number, selectors.run];
            var nonEmptyCheckFieldSelectors = [selectors.name, selectors.org, selectors.number, selectors.run];

            toggleSaveButton = function (is_enabled) {
                var is_disabled = !is_enabled;
                $(selectors.save).toggleClass(classes.disabled, is_disabled).attr('aria-disabled', is_disabled);
            };

            // Ensure that key fields passes checkTotalKeyLengthViolations check
            validateTotalKeyLength = function () {
                ViewUtils.checkTotalKeyLengthViolations(
                    selectors, classes,
                    keyFieldSelectors,
                    keyLengthViolationMessage
                );
            };

            setFieldInErr = function (element, message) {
                if (message) {
                    element.addClass(classes.error);
                    element.children(selectors.tipError).addClass(classes.showing).removeClass(classes.hiding).text(message);
                    toggleSaveButton(false);
                }
                else {
                    element.removeClass(classes.error);
                    element.children(selectors.tipError).addClass(classes.hiding).removeClass(classes.showing);
                    // One "error" div is always present, but hidden or shown
                    if ($(selectors.error).length === 1) {
                        toggleSaveButton(true);
                    }
                }
            };

            // One final check for empty values
            hasInvalidRequiredFields = function () {
                return _.reduce(
                    nonEmptyCheckFieldSelectors,
                    function (acc, element) {
                        var $element = $(element);
                        var error = validateRequiredField($element.val());
                        setFieldInErr($element.parent(), error);
                        return error ? true : acc;
                    },
                    false
                );
            };

            create = function (courseInfo, errorHandler) {
                $.postJSON(
                    '/course/',
                    courseInfo,
                    function (data) {
                        if (data.url !== undefined) {
                            ViewUtils.redirect(data.url);
                        } else if (data.ErrMsg !== undefined) {
                            errorHandler(data.ErrMsg);
                        }
                    }
                );
            };

            // Ensure that all fields are not empty
            validateFilledFields = function () {
                return _.reduce(
                    nonEmptyCheckFieldSelectors,
                    function (acc, element) {
                        var $element = $(element);
                        return $element.val().length !== 0 ? acc : false;
                    },
                    true
                );
            };

            // Handle validation asynchronously
            configureHandlers = function () {
                _.each(
                    keyFieldSelectors,
                    function (element) {
                        var $element = $(element);
                        $element.on('keyup', function (event) {
                            // Don't bother showing "required field" error when
                            // the user tabs into a new field; this is distracting
                            // and unnecessary
                            if (event.keyCode === $.ui.keyCode.TAB) {
                                return;
                            }
                            var error = validateURLItemEncoding($element.val(), $(selectors.allowUnicode).val() === 'True');
                            setFieldInErr($element.parent(), error);
                            validateTotalKeyLength();
                            if (!validateFilledFields()) {
                                toggleSaveButton(false);
                            }
                        });
                    }
                );
                var $name = $(selectors.name);
                $name.on('keyup', function () {
                    var error = validateRequiredField($name.val());
                    setFieldInErr($name.parent(), error);
                    validateTotalKeyLength();
                    if (!validateFilledFields()) {
                        toggleSaveButton(false);
                    }
                });
            };

            return {
                validateTotalKeyLength: validateTotalKeyLength,
                setFieldInErr: setFieldInErr,
                hasInvalidRequiredFields: hasInvalidRequiredFields,
                create: create,
                validateFilledFields: validateFilledFields,
                configureHandlers: configureHandlers
            };
        };
    });
