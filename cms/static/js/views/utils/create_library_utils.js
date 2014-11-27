/**
 * Provides utilities for validating libraries during creation.
 */
define(["jquery", "underscore", "gettext", "js/views/utils/view_utils"],
    function ($, _, gettext, ViewUtils) {
        return function (selectors, classes) {
            var validateTotalKeyLength, setNewLibraryFieldInErr, hasInvalidRequiredFields,
                createLibrary, validateFilledFields, configureHandlers;

            var validateRequiredField = ViewUtils.validateRequiredField;
            var validateURLItemEncoding = ViewUtils.validateURLItemEncoding;

            // Ensure that org/librarycode < 65 chars.
            validateTotalKeyLength = function () {
                var totalLength = _.reduce(
                    [selectors.org, selectors.number],
                    function (sum, ele) {
                        return sum + $(ele).val().length;
                    }, 0
                );
                if (totalLength > 65) {
                    $(selectors.errorWrapper).addClass(classes.shown).removeClass(classes.hiding);
                    $(selectors.errorMessage).html('<p>' + gettext('The combined length of the organization and library code fields cannot be more than 65 characters.') + '</p>');
                    $(selectors.save).addClass(classes.disabled);
                }
                else {
                    $(selectors.errorWrapper).removeClass(classes.shown).addClass(classes.hiding);
                }
            };

            setNewLibraryFieldInErr = function (el, msg) {
                if (msg) {
                    el.addClass(classes.error);
                    el.children(selectors.tipError).addClass(classes.showing).removeClass(classes.hiding).text(msg);
                    $(selectors.save).addClass(classes.disabled);
                }
                else {
                    el.removeClass(classes.error);
                    el.children(selectors.tipError).addClass(classes.hiding).removeClass(classes.showing);
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
                    function (acc, ele) {
                        var $ele = $(ele);
                        var error = validateRequiredField($ele.val());
                        setNewLibraryFieldInErr($ele.parent(), error);
                        return error ? true : acc;
                    },
                    false
                );
            };

            createLibrary = function (libraryInfo, errorHandler) {
                $.postJSON(
                    '/library/',
                    libraryInfo,
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
                    [selectors.org, selectors.number, selectors.name],
                    function (acc, ele) {
                        var $ele = $(ele);
                        return $ele.val().length !== 0 ? acc : false;
                    },
                    true
                );
            };

            // Handle validation asynchronously
            configureHandlers = function () {
                _.each(
                    [selectors.org, selectors.number],
                    function (ele) {
                        var $ele = $(ele);
                        $ele.on('keyup', function (event) {
                            // Don't bother showing "required field" error when
                            // the user tabs into a new field; this is distracting
                            // and unnecessary
                            if (event.keyCode === 9) {
                                return;
                            }
                            var error = validateURLItemEncoding($ele.val(), $(selectors.allowUnicode).val() === 'True');
                            setNewLibraryFieldInErr($ele.parent(), error);
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
