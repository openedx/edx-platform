define([
        'backbone',
        'jquery',
        'underscore',
        'js/programs/utils/constants',
        'text!templates/programs/confirm_modal.underscore',
        'edx-ui-toolkit/js/utils/html-utils',
        'gettext'
    ],
    function( Backbone, $, _, constants, ModalTpl, HtmlUtils ) {
        'use strict';

        return Backbone.View.extend({
            events: {
                'click .js-cancel': 'destroy',
                'click .js-confirm': 'confirm',
                'keydown': 'handleKeydown'
            },

            tpl: HtmlUtils.template( ModalTpl ),

            initialize: function( options ) {
                this.$parentEl = $( options.parentEl );
                this.callback = options.callback;
                this.content = options.content;
                this.render();
            },

            render: function() {
                HtmlUtils.setHtml(this.$el, this.tpl( this.content ));
                HtmlUtils.setHtml(this.$parentEl, HtmlUtils.HTML(this.$el));
                this.postRender();
            },

            postRender: function() {
                this.$el.find('.js-focus-first').focus();
            },

            confirm: function() {
                this.callback();
                this.destroy();
            },

            destroy: function() {
                this.undelegateEvents();
                this.remove();
                this.$parentEl.html('');
            },

            handleKeydown: function( event ) {
                var keyCode = event.keyCode;

                if ( keyCode === constants.keyCodes.esc ) {
                    this.destroy();
                }
            }
        });
    }
);
