var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccessView = Backbone.View.extend({
        el: '#login-and-registration-container',

        tpl: $('#access-tpl').html(),

        events: {
            'change .form-toggle': 'toggleForm'
        },

        subview: {
            login: {},
            register: {},
            passwordHelp: {}
        },

        // The form currently loaded
        activeForm: '',

        initialize: function( obj ) {
            this.activeForm = obj.mode;
            console.log(obj);

            this.render();
        },

        render: function() {
            $(this.el).html( _.template( this.tpl, {
                mode: this.activeForm
            }));

            this.postRender();

            return this;
        },

        postRender: function() {
            // Load the default form
            this.loadForm( this.activeForm );
            this.$header = $(this.el).find('.js-login-register-header');
        },

        loadForm: function( type ) {
            if ( type === 'login' ) {
                this.subview.login =  new edx.student.account.LoginView();

                // Listen for 'password-help' event to toggle sub-views
                this.listenTo( this.subview.login, 'password-help', this.resetPassword );
            } else if ( type === 'register' ) {
                this.subview.register = new edx.student.account.RegisterView();
            } else if ( type === 'reset' ) {
                this.subview.passwordHelp = new edx.student.account.PasswordResetView();

                // Listen for 'password-reset' event to toggle sub-views
                this.listenTo( this.subview.passwordHelp, 'password-reset', this.removePasswordView);
            }
        },

        removePasswordView: function() {
            this.$header.removeClass('hidden');
            $(this.el).find('.form-type').removeClass('hidden');

            // User should only have to submit reset once so remove view
            this.subview.passwordHelp.remove();
        },

        resetPassword: function() {
            console.log( this.$header );
            this.$header.addClass('hidden');
            $(this.el).find('.form-type').addClass('hidden');
            this.loadForm('reset');
        },

        toggleForm: function( e ) {
            var type = $(e.currentTarget).val(),
                $form = $('#' + type + '-form');

            if ( !this.form.isLoaded( $form ) ) {
                this.loadForm( type );
            }

            $(this.el).find('.form-wrapper').addClass('hidden');
            $form.removeClass('hidden');
        },

        getModel: function( type ) {
            var models = {
                join: app.JoinModel,
                login: app.JoinModel
            };

            return models[type] ? new models[type]() : false;
        },

        form: {
            isLoaded: function( $form ) {
                return $form.html().length > 0;
            }
        }
    });

})(jQuery, _, Backbone, gettext);