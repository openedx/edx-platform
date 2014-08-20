/**
 * Provides utilities for validating courses during creation, for both new courses and reruns.
 */
define(["jquery", "underscore", "gettext", "js/views/utils/view_utils"],
    function ($, _, gettext, ViewUtils) {
        return function (selectors, classes) {
            var validateRequiredField, validateCourseItemEncoding, validateTotalCourseItemsLength, setNewCourseFieldInErr,
                hasInvalidRequiredFields, createCourse, validateFilledFields, configureHandlers;

            validateRequiredField = function (msg) {
                return msg.length === 0 ? gettext('Required field.') : '';
            };

            // Check that a course (org, number, run) doesn't use any special characters
            validateCourseItemEncoding = function (item) {
                var required = validateRequiredField(item);
                if (required) {
                    return required;
                }
                if ($(selectors.allowUnicode).val() === 'True') {
                    if (/\s/g.test(item)) {
                        return gettext('Please do not use any spaces in this field.');
                    }
                }
                else {
                    if (item !== encodeURIComponent(item)) {
                        return gettext('Please do not use any spaces or special characters in this field.');
                    }
                }
                return '';
            };

            // Ensure that org/course_num/run < 65 chars.
            validateTotalCourseItemsLength = function () {
                var totalLength = _.reduce(
                    [selectors.org, selectors.number, selectors.run],
                    function (sum, ele) {
                        return sum + $(ele).val().length;
                    }, 0
                );
                if (totalLength > 65) {
                    $(selectors.errorWrapper).addClass(classes.shown).removeClass(classes.hiding);
                    $(selectors.errorMessage).html('<p>' + gettext('The combined length of the organization, course number, and course run fields cannot be more than 65 characters.') + '</p>');
                    $(selectors.save).addClass(classes.disabled);
                }
                else {
                    $(selectors.errorWrapper).removeClass(classes.shown).addClass(classes.hiding);
                }
            };

            setNewCourseFieldInErr = function (el, msg) {
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
                    [selectors.name, selectors.org, selectors.number, selectors.run],
                    function (acc, ele) {
                        var $ele = $(ele);
                        var error = validateRequiredField($ele.val());
                        setNewCourseFieldInErr($ele.parent(), error);
                        return error ? true : acc;
                    },
                    false
                );
            };

            createCourse = function (courseInfo, errorHandler) {
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
                    [selectors.org, selectors.number, selectors.run, selectors.name],
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
                    [selectors.org, selectors.number, selectors.run],
                    function (ele) {
                        var $ele = $(ele);
                        $ele.on('keyup', function (event) {
                            // Don't bother showing "required field" error when
                            // the user tabs into a new field; this is distracting
                            // and unnecessary
                            if (event.keyCode === 9) {
                                return;
                            }
                            var error = validateCourseItemEncoding($ele.val());
                            setNewCourseFieldInErr($ele.parent(), error);
                            validateTotalCourseItemsLength();
                            if (!validateFilledFields()) {
                                $(selectors.save).addClass(classes.disabled);
                            }
                        });
                    }
                );
                var $name = $(selectors.name);
                $name.on('keyup', function () {
                    var error = validateRequiredField($name.val());
                    setNewCourseFieldInErr($name.parent(), error);
                    validateTotalCourseItemsLength();
                    if (!validateFilledFields()) {
                        $(selectors.save).addClass(classes.disabled);
                    }
                });
            };

            return {
                validateRequiredField: validateRequiredField,
                validateCourseItemEncoding: validateCourseItemEncoding,
                validateTotalCourseItemsLength: validateTotalCourseItemsLength,
                setNewCourseFieldInErr: setNewCourseFieldInErr,
                hasInvalidRequiredFields: hasInvalidRequiredFields,
                createCourse: createCourse,
                validateFilledFields: validateFilledFields,
                configureHandlers: configureHandlers
            };
        };
    });
