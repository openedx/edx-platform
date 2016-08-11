(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'underscore.string',
        'gettext'
    ],
        function($, _, _s, gettext) {
            var utils;

        /* Mix non-conflicting functions from underscore.string
         * (all but include, contains, and reverse) into the
         * Underscore namespace. In practice, this mixin is done
         * by the access view, but doing it here helps keep the
         * utility self-contained.
         */
            _.mixin(_s.exports());

            utils = (function() {
                var _fn = {
                    validate: {

                        template: _.template('<li><%= content %></li>'),

                        msg: {
                            email: gettext("The email address you've provided isn't formatted correctly."),
                            min: gettext('%(field)s must have at least %(count)d characters.'),
                            max: gettext('%(field)s can only contain up to %(count)d characters.'),
                            required: gettext('Please enter your %(field)s.')
                        },

                        field: function(el) {
                            var $el = $(el),
                                required = true,
                                min = true,
                                max = true,
                                email = true,
                                response = {},
                                isBlank = _fn.validate.isBlank($el);

                            if (_fn.validate.isRequired($el)) {
                                if (isBlank) {
                                    required = false;
                                } else {
                                    min = _fn.validate.str.minlength($el);
                                    max = _fn.validate.str.maxlength($el);
                                    email = _fn.validate.email.valid($el);
                                }
                            } else if (!isBlank) {
                                min = _fn.validate.str.minlength($el);
                                max = _fn.validate.str.maxlength($el);
                                email = _fn.validate.email.valid($el);
                            }

                            response.isValid = required && min && max && email;

                            if (!response.isValid) {
                                _fn.validate.removeDefault($el);

                                response.message = _fn.validate.getMessage($el, {
                                    required: required,
                                    min: min,
                                    max: max,
                                    email: email
                                });
                            }

                            return response;
                        },

                        str: {
                            minlength: function($el) {
                                var min = $el.attr('minlength') || 0;

                                return min <= $el.val().length;
                            },

                            maxlength: function($el) {
                                var max = $el.attr('maxlength') || false;

                                return (!!max) ? max >= $el.val().length : true;
                            }
                        },

                        isRequired: function($el) {
                            return $el.attr('required');
                        },

                        isBlank: function($el) {
                            var type = $el.attr('type'),
                                isBlank;

                            if (type === 'checkbox') {
                                isBlank = !$el.prop('checked');
                            } else if (type === 'select') {
                                isBlank = ($el.data('isdefault') === true);
                            } else {
                                isBlank = !$el.val();
                            }

                            return isBlank;
                        },

                        email: {
                        // This is the same regex used to validate email addresses in Django 1.4
                            regex: new RegExp(
                            [
                                '(^[-!#$%&\'*+/=?^_`{}|~0-9A-Z]+(\\.[-!#$%&\'*+/=?^_`{}|~0-9A-Z]+)*',
                                '|^"([\\001-\\010\\013\\014\\016-\\037!#-\\[\\]-\\177]|\\\\[\\001-\\011\\013\\014\\016-\\177])*"',
                                ')@((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[A-Z]{2,9}\\.?$)',
                                '|\\[(25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)(\\.(25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)){3}\\]$'
                            ].join(''), 'i'
                        ),

                            valid: function($el) {
                                return $el.attr('type') === 'email' ? _fn.validate.email.format($el.val()) : true;
                            },

                            format: function(str) {
                                return _fn.validate.email.regex.test(str);
                            }
                        },

                        getLabel: function(id) {
                        // Extract the field label, remove the asterisk (if it appears) and any extra whitespace
                            return $('label[for=' + id + ']').text().split('*')[0].trim();
                        },

                        getMessage: function($el, tests) {
                            var txt = [],
                                label,
                                context,
                                content,
                                customMsg;

                            _.each(tests, function(value, key) {
                                if (!value) {
                                    label = _fn.validate.getLabel($el.attr('id'));
                                    customMsg = $el.data('errormsg-' + key) || false;

                                // If the field has a custom error msg attached, use it
                                    if (customMsg) {
                                        content = customMsg;
                                    } else {
                                        context = {field: label};

                                        if (key === 'min') {
                                            context.count = parseInt($el.attr('minlength'), 10);
                                        } else if (key === 'max') {
                                            context.count = parseInt($el.attr('maxlength'), 10);
                                        }

                                        content = _.sprintf(_fn.validate.msg[key], context);
                                    }

                                    txt.push(_fn.validate.template({content: content}));
                                }
                            });

                            return txt.join(' ');
                        },

                    // Removes the default HTML5 validation pop-up
                        removeDefault: function($el) {
                            if ($el.setCustomValidity) {
                                $el.setCustomValidity(' ');
                            }
                        }
                    }
                };

                return {
                    validate: _fn.validate.field
                };
            })();

            return utils;
        });
}).call(this, define || RequireJS.define);
