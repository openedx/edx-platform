var edx = edx || {};

(function($, _, _s, Backbone, gettext) {
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
            /* Mix non-conflicting functions from underscore.string
             * (all but include, contains, and reverse) into the
             * Underscore namespace
             */
            _.mixin( _s.exports() );

            this.tpl = $(this.tpl).html();
            this.activeForm = obj.mode || 'login';
            this.thirdPartyAuth = obj.thirdPartyAuth || {
                currentProvider: null,
                providers: []
            };
            this.platformName = obj.platformName;

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
            this.getFormData( type, this.load[type], this );
        },

        load: {
            login: function( data, context ) {
                var model = new edx.student.account.LoginModel({
                    url: data.submit_url
                });

                context.subview.login =  new edx.student.account.LoginView({
                    fields: data.fields,
                    model: model,
                    thirdPartyAuth: context.thirdPartyAuth,
                    platformName: context.platformName
                });

                // Listen for 'password-help' event to toggle sub-views
                context.listenTo( context.subview.login, 'password-help', context.resetPassword );
            },

            reset: function( data, context ) {
                var model = new edx.student.account.PasswordResetModel({
                    url: data.submit_url
                });

                context.subview.passwordHelp = new edx.student.account.PasswordResetView({
                    fields: data.fields,
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
                    thirdPartyAuth: context.thirdPartyAuth,
                    platformName: context.platformName
                });
            }
        },

        getFormData: function( type, callback, context ) {
            var urls = {
                login: 'login_session',
                register: 'registration',
                reset: 'password_reset'
            };

            $.ajax({
                url: '/user_api/v1/account/' + urls[type] + '/',
                type: 'GET',
                dataType: 'json'
            })
            .done(function( data ) {
                callback( data, context );
            })
            .fail(function( jqXHR, textStatus, errorThrown ) {
                console.log('fail ', errorThrown);
            });
        },

        resetPassword: function() {
            window.analytics.track('edx.bi.password_reset_form.viewed', {
                category: 'user-engagement'
            });

            this.element.hide( this.$header );
            this.element.hide( $(this.el).find('.form-type') );
            this.loadForm('reset');
        },

        toggleForm: function( e ) {
            var type = $(e.currentTarget).val(),
                $form = $('#' + type + '-form'),
                $anchor = $('#' + type + '-anchor');

            window.analytics.track('edx.bi.' + type + '_form.toggled', {
                category: 'user-engagement'
            });

            if ( !this.form.isLoaded( $form ) ) {
                this.loadForm( type );
            }

            this.element.hide( $(this.el).find('.form-wrapper') );
            this.element.show( $form );

            // Scroll to top of selected form
            $('html,body').animate({
                scrollTop: $anchor.offset().top
            },'slow');
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
})(jQuery, _, _.str, Backbone, gettext);
