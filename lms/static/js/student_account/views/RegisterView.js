var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.RegisterView = Backbone.View.extend({
        tagName: 'form',

        el: '#register-form',

        tpl: '#register-tpl',

        fieldTpl: $('#form_field-tpl').html(),

        events: {
            'click .js-register': 'submitForm',
            'click .login-provider': 'thirdPartyAuth'
        },

        errors: [],

        $form: {},

        initialize: function( thirdPartyAuthInfo ) {
            this.tpl = $(this.tpl).html();

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
        },

        getInitialData: function() {
            var that = this;

            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '/user_api/v1/account/registration/',
                success: function( data ) {
                    console.log(data);
                    that.buildForm( data.fields );
                    that.initModel( data.submit_url, data.method );
                },
                error: function( jqXHR, textStatus, errorThrown ) {
                    console.log('fail ', errorThrown);
                }
            });
        },

        initModel: function( url ) {
            this.model = new edx.student.account.RegisterModel({
                url: url
            });

            this.listenTo( this.model, 'error', function( error ) {
                console.log(error.status, ' error: ', error.responseText);
            });
        },

        buildForm: function( data ) {
            var html = [],
                i,
                len = data.length,
                fieldTpl = this.fieldTpl;
            for ( i=0; i<len; i++ ) {
                // "default" is reserved in JavaScript
                data[i].value = data[i]["default"];

                html.push( _.template( fieldTpl, $.extend( data[i], {
                    form: 'register'
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

        submitForm: function( event ) {
            var data = this.getFormData();

            event.preventDefault();
console.log(data);
            // console.log(this.model);

            if ( !this.errors.length ) {
                console.log('save me');
                this.model.set( data );
console.log(this.model);
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
        }
    });

})(jQuery, _, Backbone, gettext);