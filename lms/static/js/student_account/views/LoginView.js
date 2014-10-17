var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.LoginView = Backbone.View.extend({
        tagName: 'form',

        el: '#login-form',

        tpl: $('#login-tpl').html(),

        fieldTpl: $('#form_field-tpl').html(),

        events: {
            'click .js-login': 'submitForm',
            'click .forgot-password': 'forgotPassword'
        },

        errors: [],

        $form: {},

        initialize: function( obj ) {
            this.getInitialData();
        },

        // Renders the form.
        render: function( html ) {
            var fields = html || '';

            $(this.el).html( _.template( this.tpl, {
                fields: fields
            }));

            this.postRender();

            return this;
        },

        postRender: function() {

            this.$form = $(this.el).find('form');
        },

        getInitialData: function() {
            var that = this;

            $.ajax({
                type: 'GET',
                dataType: 'json',
                url: '/user_api/v1/account/login_session/',
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

        initModel: function( url, method ) {
            this.model = new edx.student.account.LoginModel({
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
                if ( data[i].name === 'password' ) {
                    data[i].type = 'password';
                }

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
                    // if ( this.validate( elements[i] ) ) {
                        obj[key] = $el.attr('type') === 'checkbox' ? $el.is(':checked') : $el.val();
                    //     $el.css('border', '1px solid #ccc');
                    // } else {
                    //     errors.push( key );
                    //     $el.css('border', '2px solid red');
                    // }
                }
            }

            //this.errors = errors;

            return obj;
        },

        forgotPassword: function( event ) {
            event.preventDefault();
            console.log('forgotPassword');
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

        toggleErrorMsg: function( show ) {
            if ( show ) {
                console.log('show');
            } else {
                console.log('hide');
            }
        }
    });

})(jQuery, _, Backbone, gettext);