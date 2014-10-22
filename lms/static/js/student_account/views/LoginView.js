var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.LoginView = Backbone.View.extend({
        tagName: 'form',

        el: '#login-form',

        tpl: '#login-tpl',

        fieldTpl: '#form_field-tpl',

        events: {
            'click .js-login': 'submitForm',
            'click .forgot-password': 'forgotPassword',
            'click .login-provider': 'thirdPartyAuth'
        },

        errors: [],

        $form: {},

        initialize: function( thirdPartyAuthInfo ) {
            this.tpl = $(this.tpl).html();
            this.fieldTpl = $(this.fieldTpl).html();

            this.providers = thirdPartyAuthInfo.providers || [];
            this.currentProvider = thirdPartyAuthInfo.currentProvider || "";

            this.getInitialData();
        },

        // Renders the form.
        render: function( html ) {
            var fields = html || '';

            $(this.el).html( _.template( this.tpl, {
                fields: fields,
                currentProvider: this.currentProvider,
                providers: this.providers
            }));

            this.postRender();

            return this;
        },

        postRender: function() {
            var $container = $(this.el);
            this.$form = $container.find('form');
            this.$errors = $container.find('.error-msg');
            this.$alreadyAuthenticatedMsg =  $container.find('.already-authenticated-msg');

            // If we're already authenticated with a third-party
            // provider, try logging in.  The easiest way to do this
            // is to simply submit the form.
            if (this.currentProvider) {
                this.model.save();
            }
        },

        getInitialData: function() {
            var that = this;

            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '/user_api/v1/account/login_session/',
                success: function( data ) {
                    console.log(data);
                    that.initModel( data.submit_url, data.method );
                    that.buildForm( data.fields );
                },
                error: function( jqXHR, textStatus, errorThrown ) {
                    console.log('fail ', errorThrown);
                }
            });
        },

        initModel: function( url ) {
            this.model = new edx.student.account.LoginModel({
                url: url
            });

            this.listenTo( this.model, 'error', this.saveError );
        },

        buildForm: function( data ) {
            var html = [],
                i,
                len = data.length,
                fieldTpl = this.fieldTpl;

            for ( i=0; i<len; i++ ) {
                html.push( _.template( fieldTpl, $.extend( data[i], {
                    form: 'login'
                }) ) );
            }

            this.render( html.join('') );
        },

        getFormData: function() {

            var obj = {},
                $form = this.$form,
                elements = $form[0].elements,
                i,
                len = elements.length,
                $el,
                key = '',
                errors = [];

            for ( i=0; i<len; i++ ) {

                $el = $( elements[i] );
                key = $el.attr('name') || false;

                if ( key ) {
                    if ( this.validate( elements[i] ) ) {
                        obj[key] = $el.attr('type') === 'checkbox' ? $el.is(':checked') : $el.val();
                        $el.css('border', '1px solid #ccc');
                    } else {
                        errors.push( key );
                        $el.css('border', '2px solid red');
                    }
                }
            }

            this.errors = errors;

            return obj;
        },

        forgotPassword: function( event ) {
            event.preventDefault();

            this.trigger('password-help');
        },

        submitForm: function( event ) {
            var data = this.getFormData();

            event.preventDefault();

            // console.log(this.model);

            if ( !this.errors.length ) {
                console.log('save me');
                this.model.set( data );
                this.model.save();
                this.toggleErrorMsg( false );
            } else {
                console.log('here are the errors ', this.errors);
                this.toggleErrorMsg( true );
            }
        },

        thirdPartyAuth: function( event ) {
            var providerUrl = $(event.target).data("provider-url") || "";
            if (providerUrl) {
                window.location.href = providerUrl;
            } else {
                // TODO -- error handling here
                console.log("No URL available for third party auth provider");
            }
        },

        toggleErrorMsg: function( show ) {
            if ( show ) {
                this.$errors.removeClass('hidden');
            } else {
                this.$errors.addClass('hidden');
            }
        },

        validate: function( $el ) {
            return edx.utils.validate( $el );
        },

        saveError: function( error ) {
            console.log(error.status, ' error: ', error.responseText);

            // If we've gotten a 401 error, it means that we've successfully
            // authenticated with a third-party provider, but we haven't
            // linked the account to an EdX account.  In this case,
            // we need to prompt the user to enter a little more information
            // to complete the registration process.
            if (error.status === 401 && this.currentProvider) {
                this.$alreadyAuthenticatedMsg.removeClass("hidden");
            }
            else {
                this.$alreadyAuthenticatedMsg.addClass("hidden");
                // TODO -- display the error
            }
        }
    });

})(jQuery, _, Backbone, gettext);