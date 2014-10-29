/**
 * Provides utilities for validating libraries during creation.
 */
define(["jquery", "underscore", "gettext", "js/views/utils/view_utils"],
    function ($, _, gettext, ViewUtils) {
        "use strict";
        return function (selectors, classes) {
            var validateTotalKeyLength, setNewLibraryFieldInErr, hasInvalidRequiredFields,
                createLibrary, validateFilledFields, configureHandlers;

            var validateRequiredField = ViewUtils.validateRequiredField;
            var validateURLItemEncoding = ViewUtils.validateURLItemEncoding;

            var keyLengthViolationMessage = gettext("The combined length of the organization and library code fields cannot be more than <%=limit%> characters.");

            // Ensure that org/librarycode passes validateTotalKeyLength check
            validateTotalKeyLength = function () {
                ViewUtils.checkTotalKeyLengthViolations(
                    selectors, classes,
                    [selectors.org, selectors.number],
                    keyLengthViolationMessage
                );
            };

            setNewLibraryFieldInErr = function (element, message) {
                if (message) {
                    element.addClass(classes.error);
                    element.children(selectors.tipError).addClass(classes.showing).removeClass(classes.hiding).text(message);
                    $(selectors.save).addClass(classes.disabled);
                }
                else {
                    element.removeClass(classes.error);
                    element.children(selectors.tipError).addClass(classes.hiding).removeClass(classes.showing);
                    // One "error" div is always present, but hidden or shown
                    if ($(selectors.error).length === 1) {
                        $(selectors.save).removeClass(classes.disabled);
                    }
                }
            };

            // One final check for empty values
            hasInvalidRequiredFields = function () {
                return _.reduce(
                    [selectors.name, selectors.org, selectors.number],
                    function (acc, element) {
                        var $element = $(element);
                        var error = validateRequiredField($element.val());
                        setNewLibraryFieldInErr($element.parent(), error);
                        return error ? true : acc;
                    },
                    false
                );
            };

            createLibrary = function (libraryInfo, errorHandler) {
                $.postJSON(
                    '/library/',
                    libraryInfo
                ).done(function (data) {
                    ViewUtils.redirect(data.url);
                }).fail(function(jqXHR, textStatus, errorThrown) {
                    var reason = errorThrown;
                    if (jqXHR.responseText) {
                        try {
                            var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                            if (detailedReason) {
                                reason = detailedReason;
                            }
                        } catch (e) {}
                    }
                    errorHandler(reason);
                });
            };

            // Ensure that all fields are not empty
            validateFilledFields = function () {
                return _.reduce(
                    [selectors.org, selectors.number, selectors.name],
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
                    [selectors.org, selectors.number],
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
                            setNewLibraryFieldInErr($element.parent(), error);
                            validateTotalKeyLength();
                            if (!validateFilledFields()) {
                                $(selectors.save).addClass(classes.disabled);
                            }
                        });
                    }
                );
                var $name = $(selectors.name);
                $name.on('keyup', function () {
                    var error = validateRequiredField($name.val());
                    setNewLibraryFieldInErr($name.parent(), error);
                    validateTotalKeyLength();
                    if (!validateFilledFields()) {
                        $(selectors.save).addClass(classes.disabled);
                    }
                });
            };

            return {
                validateTotalKeyLength: validateTotalKeyLength,
                setNewLibraryFieldInErr: setNewLibraryFieldInErr,
                hasInvalidRequiredFields: hasInvalidRequiredFields,
                createLibrary: createLibrary,
                validateFilledFields: validateFilledFields,
                configureHandlers: configureHandlers
            };
        };
    });
