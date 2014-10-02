var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.profile = {};

    edx.student.profile.ProfileModel = Backbone.Model.extend({
        defaults: {
            fullName: ''
        },

        urlRoot: '',

        sync: function(method, model) {
            var headers = {
                'X-CSRFToken': $.cookie('csrftoken')
            };

            $.ajax({
                url: model.urlRoot,
                type: 'PUT',
                data: model.attributes,
                headers: headers
            })
            .done(function() {
                model.trigger('sync');
            })
            .fail(function() {
                var error = gettext("The data could not be saved.");
                model.trigger('error', error);
            });
        },

        validate: function(attrs) {
            var errors = {};
            if (attrs.fullName.length < 1) {
                errors.fullName = gettext("Full name cannot be blank");
            }

            if (!$.isEmptyObject(errors)) {
                return errors;
            }
        }
    });

    edx.student.profile.ProfileView = Backbone.View.extend({

        events: {
            'submit': 'submit',
            'change': 'change'
        },

        initialize: function() {
            _.bindAll(this, 'render', 'change', 'submit', 'invalid', 'error', 'sync', 'clearStatus');
            this.model = new edx.student.profile.ProfileModel();
            this.model.on('invalid', this.invalid);
            this.model.on('error', this.error);
            this.model.on('sync', this.sync);
        },

        render: function() {
            this.$el.html(_.template($('#profile-tpl').html(), {}));
            this.$nameStatus = $('#profile-name-status', this.$el);
            this.$nameField = $('#profile-name', this.$el);
            this.$submitStatus = $('#submit-status', this.$el);
            return this;
        },

        change: function() {
            this.model.set({
                fullName: this.$nameField.val()
            });
        },

        submit: function(event) {
            event.preventDefault();
            this.clearStatus();
            this.model.save();
        },

        invalid: function(model) {
            var errors = model.validationError;
            if (errors.hasOwnProperty('fullName')) {
                this.$nameStatus
                    .addClass('validation-error')
                    .text(errors.fullName);
            }
        },

        error: function(error) {
            this.$submitStatus
                .addClass('error')
                .text(error);
        },

        sync: function() {
            this.$submitStatus
                .addClass('success')
                .text(gettext("Saved"));
        },

        clearStatus: function() {
            this.$nameStatus
                .removeClass('validation-error')
                .text("");

            this.$submitStatus
                .removeClass('error')
                .text("");
        }
    });

    return new edx.student.profile.ProfileView({
        el: $('#profile-container')
    }).render();

})(jQuery, _, Backbone, gettext);
