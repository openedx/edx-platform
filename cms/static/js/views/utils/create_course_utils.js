/**
 * Provides utilities for validating courses during creation, for both new courses and reruns.
 */
define(["jquery", "underscore", "gettext", "js/views/utils/view_utils"],
    function ($, _, gettext, ViewUtils) {
        return function (selectors, classes) {
            var validateTotalCourseItemsLength, setNewCourseFieldInErr, hasInvalidRequiredFields,
                createCourse, validateFilledFields, configureHandlers;

            var validateRequiredField = ViewUtils.validateRequiredField;
            var validateURLItemEncoding = ViewUtils.validateURLItemEncoding;

            var keyLengthViolationMessage = gettext('The combined length of the organization, course number, and course run fields cannot be more than <%=limit%> characters.');

            // Ensure that org, course_num and run passes checkTotalKeyLengthViolations
            validateTotalCourseItemsLength = function () {
                ViewUtils.checkTotalKeyLengthViolations(
                    selectors, classes,
                    [selectors.org, selectors.number, selectors.run],
                    keyLengthViolationMessage
                );
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
                            var error = validateURLItemEncoding($ele.val(), $(selectors.allowUnicode).val() === 'True');
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
                validateTotalCourseItemsLength: validateTotalCourseItemsLength,
                setNewCourseFieldInErr: setNewCourseFieldInErr,
                hasInvalidRequiredFields: hasInvalidRequiredFields,
                createCourse: createCourse,
                validateFilledFields: validateFilledFields,
                configureHandlers: configureHandlers
            };
        };
    });
