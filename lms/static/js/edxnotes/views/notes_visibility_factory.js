(function(define, undefined) {
    'use strict';
    define([
        'jquery', 'underscore', 'backbone', 'gettext',
        'annotator_1.2.9', 'js/edxnotes/views/visibility_decorator', 'js/utils/animation'
    ], function($, _, Backbone, gettext, Annotator, VisibilityDecorator) {
        var ToggleVisibilityView = Backbone.View.extend({
            events: {
                'click .action-toggle-notes': 'toggleHandler'
            },

            errorMessage: gettext('An error has occurred. Make sure that you are connected to the Internet, and then try refreshing the page.'),

            initialize: function(options) {
                _.bindAll(this, 'onSuccess', 'onError', 'keyDownToggleHandler');
                this.visibility = options.visibility;
                this.visibilityUrl = options.visibilityUrl;
                this.label = this.$('.utility-control-label');
                this.actionLink = this.$('.action-toggle-notes');
                this.actionLink.removeClass('is-disabled');
                this.actionToggleMessage = this.$('.action-toggle-message');
                this.notification = new Annotator.Notification();
                $(document).on('keydown.edxnotes:togglenotes', this.keyDownToggleHandler);
            },

            remove: function() {
                $(document).off('keydown.edxnotes:togglenotes');
                Backbone.View.prototype.remove.call(this);
            },

            toggleHandler: function(event) {
                debugger;
                event.preventDefault();
                this.visibility = !this.visibility;
                AnimationUtil.triggerAnimation(this.actionToggleMessage);
                this.toggleNotes(this.visibility);
            },

            keyDownToggleHandler: function(event) {
            // Character '[' has keyCode 219
                if (event.keyCode === 219 && event.ctrlKey && event.shiftKey) {
                    this.toggleHandler(event);
                }
            },

            toggleNotes: function(visibility) {
                if (visibility) {
                    this.enableNotes();
                } else {
                    this.disableNotes();
                }
                this.sendRequest();
            },

            enableNotes: function() {
                VisibilityDecorator.enableNote();
                this.actionLink.addClass('is-active');
                this.label.text(gettext('Hide notes'));
                this.actionToggleMessage.text(gettext('Notes visible'));
            },

            disableNotes: function() {
                VisibilityDecorator.disableNotes();
                this.actionLink.removeClass('is-active');
                this.label.text(gettext('Show notes'));
                this.actionToggleMessage.text(gettext('Notes hidden'));
            },

            hideErrorMessage: function() {
                this.notification.hide();
            },

            showErrorMessage: function(message) {
                this.notification.show(message, Annotator.Notification.ERROR);
            },

            sendRequest: function() {
                return $.ajax({
                    type: 'PUT',
                    url: this.visibilityUrl,
                    dataType: 'json',
                    data: JSON.stringify({'visibility': this.visibility}),
                    success: this.onSuccess,
                    error: this.onError
                });
            },

            onSuccess: function() {
                this.hideErrorMessage();
            },

            onError: function() {
                this.showErrorMessage(this.errorMessage);
            }
        });

        return {
            ToggleVisibilityView: function(visibility, visibilityUrl) {
                return new ToggleVisibilityView({
                    el: $('.edx-notes-visibility').get(0),
                    visibility: visibility,
                    visibilityUrl: visibilityUrl
                });
            },
            VisibilityDecorator: VisibilityDecorator
        };
    });
}).call(this, define || RequireJS.define);
