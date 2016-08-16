var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccountModel = Backbone.Model.extend({
        // These should be the same length limits enforced by the server
        EMAIL_MIN_LENGTH: 3,
        EMAIL_MAX_LENGTH: 254,
        PASSWORD_MIN_LENGTH: 2,
        PASSWORD_MAX_LENGTH: 75,

        // This is the same regex used to validate email addresses in Django 1.4
        EMAIL_REGEX: new RegExp(
            "(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*" +
            '|^"([\\001-\\010\\013\\014\\016-\\037!#-\\[\\]-\\177]|\\\\[\\001-\\011\\013\\014\\016-\\177])*"' +
            ')@((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[A-Z]{2,6}\\.?$)' +
            '|\\[(25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)(\\.(25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)){3}\\]$',
            'i'
        ),

        defaults: {
            email: '',
            password: ''
        },

        urlRoot: 'email',

        sync: function(method, model) {
            var headers = {
                'X-CSRFToken': $.cookie('csrftoken')
            };

            $.ajax({
                url: model.urlRoot,
                type: 'POST',
                data: model.attributes,
                headers: headers
            })
            .done(function() {
                model.trigger('sync');
            })
            .fail(function() {
                var error = gettext('The data could not be saved.');
                model.trigger('error', error);
            });
        },

        validate: function(attrs) {
            var errors = {};

            if (attrs.email.length < this.EMAIL_MIN_LENGTH ||
                attrs.email.length > this.EMAIL_MAX_LENGTH ||
                !this.EMAIL_REGEX.test(attrs.email)
            ) { errors.email = gettext('Please enter a valid email address'); }

            if (attrs.password.length < this.PASSWORD_MIN_LENGTH || attrs.password.length > this.PASSWORD_MAX_LENGTH) {
                errors.password = gettext('Please enter a valid password');
            }

            if (!$.isEmptyObject(errors)) {
                return errors;
            }
        }
    });

    edx.student.account.AccountView = Backbone.View.extend({

        events: {
            'submit': 'submit',
            'change': 'change',
            'click #password-reset': 'click'
        },

        initialize: function() {
            _.bindAll(this, 'render', 'submit', 'change', 'click', 'clearStatus', 'invalid', 'error', 'sync');
            this.model = new edx.student.account.AccountModel();
            this.model.on('invalid', this.invalid);
            this.model.on('error', this.error);
            this.model.on('sync', this.sync);
        },

        render: function() {
            this.$el.html(_.template($('#account-tpl').html())({}));
            this.$email = $('#new-email', this.$el);
            this.$password = $('#password', this.$el);
            this.$emailStatus = $('#new-email-status', this.$el);
            this.$passwordStatus = $('#password-status', this.$el);
            this.$requestStatus = $('#request-email-status', this.$el);
            this.$passwordReset = $('#password-reset', this.$el);
            this.$passwordResetStatus = $('#password-reset-status', this.$el);

            return this;
        },

        submit: function(event) {
            event.preventDefault();
            this.clearStatus();
            this.model.save();
        },

        change: function() {
            this.model.set({
                email: this.$email.val(),
                password: this.$password.val()
            });
        },

        click: function(event) {
            event.preventDefault();
            this.clearStatus();

            var self = this;
            $.ajax({
                url: 'password',
                type: 'POST',
                data: {},
                headers: {
                    'X-CSRFToken': $.cookie('csrftoken')
                }
            })
            .done(function() {
                self.$passwordResetStatus
                    .addClass('success')
                    .text(gettext('Password reset email sent. Follow the link in the email to change your password.'));
            })
            .fail(function() {
                self.$passwordResetStatus
                    .addClass('error')
                    .text(gettext("We weren't able to send you a password reset email."));
            });
        },

        invalid: function(model) {
            var errors = model.validationError;

            if (errors.hasOwnProperty('email')) {
                this.$emailStatus
                    .addClass('validation-error')
                    .text(errors.email);
            }

            if (errors.hasOwnProperty('password')) {
                this.$passwordStatus
                    .addClass('validation-error')
                    .text(errors.password);
            }
        },

        error: function(error) {
            this.$requestStatus
                .addClass('error')
                .text(error);
        },

        sync: function() {
            this.$requestStatus
                .addClass('success')
                .text(gettext('Please check your email to confirm the change'));
        },

        clearStatus: function() {
            this.$emailStatus
                .removeClass('validation-error')
                .text('');

            this.$passwordStatus
                .removeClass('validation-error')
                .text('');

            this.$requestStatus
                .removeClass('error')
                .text('');

            this.$passwordResetStatus
                .removeClass('error')
                .text('');
        }
    });

    try {
        new edx.student.account.AccountView({
            el: $('#account-container')
        }).render();
    } catch (e) {
        // TODO: handle exception
    }
})(jQuery, _, Backbone, gettext);
