/**
 * Mixin class for creation of things like courses and libraries.
 */
// eslint-disable-next-line no-undef
define(['jquery', 'underscore', 'gettext', 'common/js/components/utils/view_utils'],
    function($, _, gettext, ViewUtils) {
        return function(selectors, classes, keyLengthViolationMessage, keyFieldSelectors, nonEmptyCheckFieldSelectors) {
            // eslint-disable-next-line no-var
            var self = this;

            this.selectors = selectors;
            this.classes = classes;
            this.validateRequiredField = ViewUtils.validateRequiredField;
            this.validateURLItemEncoding = ViewUtils.validateURLItemEncoding;
            this.keyLengthViolationMessage = keyLengthViolationMessage;
            // Key fields for your model, like [selectors.org, selectors.number]
            this.keyFieldSelectors = keyFieldSelectors;
            // Fields that must not be empty on your model.
            this.nonEmptyCheckFieldSelectors = nonEmptyCheckFieldSelectors;

            // eslint-disable-next-line no-unused-vars
            this.create = function(courseInfo, errorHandler) {
                // Replace this with a function that will make a request to create the object.
            };

            // Ensure that key fields passes checkTotalKeyLengthViolations check
            this.validateTotalKeyLength = function() {
                ViewUtils.checkTotalKeyLengthViolations(
                    self.selectors, self.classes,
                    self.keyFieldSelectors,
                    self.keyLengthViolationMessage
                );
            };

            // eslint-disable-next-line camelcase
            this.toggleSaveButton = function(is_enabled) {
                /* eslint-disable-next-line camelcase, no-var */
                var is_disabled = !is_enabled;
                $(self.selectors.save).toggleClass(self.classes.disabled, is_disabled).attr('aria-disabled', is_disabled);
            };

            this.setFieldInErr = function(element, message) {
                if (message) {
                    element.addClass(self.classes.error);
                    element.children(self.selectors.tipError).addClass(self.classes.showing).removeClass(self.classes.hiding).text(message);
                    self.toggleSaveButton(false);
                } else {
                    element.removeClass(self.classes.error);
                    element.children(self.selectors.tipError).addClass(self.classes.hiding).removeClass(self.classes.showing);
                    // One "error" div is always present, but hidden or shown
                    if ($(self.selectors.error).length === 1) {
                        self.toggleSaveButton(true);
                    }
                }
            };

            // One final check for empty values
            this.hasInvalidRequiredFields = function() {
                return _.reduce(
                    self.nonEmptyCheckFieldSelectors,
                    function(acc, element) {
                        // eslint-disable-next-line no-var
                        var $element = $(element);
                        // eslint-disable-next-line no-var
                        var error = self.validateRequiredField($element.val());
                        self.setFieldInErr($element.parent(), error);
                        return error ? true : acc;
                    },
                    false
                );
            };

            // Ensure that all fields are not empty
            this.validateFilledFields = function() {
                return _.reduce(
                    self.nonEmptyCheckFieldSelectors,
                    function(acc, element) {
                        // eslint-disable-next-line no-var
                        var $element = $(element);
                        return $element.val().length !== 0 ? acc : false;
                    },
                    true
                );
            };

            // Handle validation asynchronously
            this.configureHandlers = function() {
                _.each(
                    self.keyFieldSelectors,
                    function(element) {
                        // eslint-disable-next-line no-var
                        var $element = $(element);
                        $element.on('keyup', function(event) {
                            // Don't bother showing "required field" error when
                            // the user tabs into a new field; this is distracting
                            // and unnecessary
                            if (event.keyCode === $.ui.keyCode.TAB) {
                                return;
                            }
                            // eslint-disable-next-line no-var
                            var error = self.validateURLItemEncoding($element.val(), $(self.selectors.allowUnicode).val() === 'True');
                            self.setFieldInErr($element.parent(), error);
                            self.validateTotalKeyLength();
                            if (!self.validateFilledFields()) {
                                self.toggleSaveButton(false);
                            }
                        });
                    }
                );

                // eslint-disable-next-line no-var
                var $name = $(self.selectors.name);
                $name.on('keyup', function() {
                    // eslint-disable-next-line no-var
                    var error = self.validateRequiredField($name.val());
                    self.setFieldInErr($name.parent(), error);
                    self.validateTotalKeyLength();
                    if (!self.validateFilledFields()) {
                        self.toggleSaveButton(false);
                    }
                });
            };

            return {
                validateTotalKeyLength: self.validateTotalKeyLength,
                setFieldInErr: self.setFieldInErr,
                hasInvalidRequiredFields: self.hasInvalidRequiredFields,
                create: self.create,
                validateFilledFields: self.validateFilledFields,
                configureHandlers: self.configureHandlers
            };
        };
    }
);
