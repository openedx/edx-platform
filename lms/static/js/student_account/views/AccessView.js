var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccessView = Backbone.View.extend({
        el: '#login-and-registration-container',

        tpl: '#access-tpl',

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
            this.tpl = $(this.tpl).html();
            this.activeForm = obj.mode || 'login';
            this.thirdPartyAuth = obj.thirdPartyAuth || {
                currentProvider: null,
                providers: []
            };

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
            if ( type === 'reset' ) {
                this.load.reset( this );
            } else {
                this.getFormData( type, this.load[type], this );
            }
        },

        load: {
            login: function( data, context ) {
                var model = new edx.student.account.LoginModel({
                    url: data.submit_url
                });

                context.subview.login =  new edx.student.account.LoginView({
                    fields: data.fields,
                    model: model,
                    thirdPartyAuth: context.thirdPartyAuth
                });

                // Listen for 'password-help' event to toggle sub-views
                context.listenTo( context.subview.login, 'password-help', context.resetPassword );
            },

            reset: function( context ) {
                var model = new edx.student.account.PasswordResetModel(),
                    data = [{
                        label: 'E-mail',
                        instructions: 'This is the e-mail address you used to register with edX',
                        name: 'email',
                        required: true,
                        type: 'email',
                        restrictions: [],
                        defaultValue: ''
                    }];

                context.subview.passwordHelp = new edx.student.account.PasswordResetView({
                    fields: data,
                    model: model
                });
            },

            register: function( data, context ) {
                var model = new edx.student.account.RegisterModel({
                    url: data.submit_url
                });

                context.subview.register =  new edx.student.account.RegisterView({
                    fields: data.fields,
                    model: model,
                    thirdPartyAuth: context.thirdPartyAuth
                });
            }
        },

        getFormData: function( type, callback, context ) {
            var urls = {
                login: 'login_session',
                register: 'registration'
            };

            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '/user_api/v1/account/' + urls[type] + '/',
                success: function( data ) {
                    callback( data, context );
                },
                error: function( jqXHR, textStatus, errorThrown ) {
                    console.log('fail ', errorThrown);
                }
            });
        },

        resetPassword: function() {
            this.element.hide( this.$header );
            this.element.hide( $(this.el).find('.form-type') );
            this.loadForm('reset');
        },

        toggleForm: function( e ) {
            var type = $(e.currentTarget).val(),
                $form = $('#' + type + '-form');

            if ( !this.form.isLoaded( $form ) ) {
                this.loadForm( type );
            }

            this.element.hide( $(this.el).find('.form-wrapper') );
            this.element.show( $form );
        },

        form: {
            isLoaded: function( $form ) {
                return $form.html().length > 0;
            }
        },

        /* Helper method ot toggle display
         * including accessibility considerations
         */
        element: {
            hide: function( $el ) {
                $el.addClass('hidden')
                   .attr('aria-hidden', true);
            },

            show: function( $el ) {
                $el.removeClass('hidden')
                   .attr('aria-hidden', false);
            }
        }
    });

})(jQuery, _, Backbone, gettext);
