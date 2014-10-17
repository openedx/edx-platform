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
        },

        loadForm: function( type ) {
            if ( type === 'login' ) {
                console.log('load login');
                return new edx.student.account.LoginView();
            }

            // return new app.LoginView({
            //     el: $('#' + type + '-form'),
            //     model: this.getModel( type ),
            //     tpl: $('#' + type + '-form-tpl').html()
            // });
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