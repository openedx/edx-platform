;(function (define, undefined) {
'use strict';
define([
    'jquery', 'underscore', 'backbone', 'gettext',
    'annotator_1.2.9', 'js/edxnotes/views/visibility_decorator'
], function($, _, Backbone, gettext, Annotator, EdxnotesVisibilityDecorator) {
    var ToggleNotesView = Backbone.View.extend({
        events: {
            'click .action-toggle-notes': 'toggleHandler'
        },

        errorMessage: gettext("An error has occurred. Make sure that you are connected to the Internet, and then try refreshing the page."),

        initialize: function (options) {
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

        toggleHandler: function (event) {
            event.preventDefault();
            this.visibility = !this.visibility;
            this.showActionMessage();
            this.toggleNotes(this.visibility);
        },

        keyDownToggleHandler: function (event) {
            // Character 'n' has keyCode 78
            if (event.keyCode === 78 && event.ctrlKey && event.altKey) {
                this.toggleHandler(event);
            }
        },

        toggleNotes: function (visibility) {
            if (visibility) {
                this.enableNotes();
            } else {
                this.disableNotes();
            }
            this.sendRequest();
        },

        showActionMessage: function () {
            // The following lines are necessary to re-trigger the CSS animation on span.action-toggle-message
            this.actionToggleMessage.removeClass('is-fleeting');
            this.actionToggleMessage.offset().width = this.actionToggleMessage.offset().width;
            this.actionToggleMessage.addClass('is-fleeting');
        },

        enableNotes: function () {
            _.each($('.edx-notes-wrapper'), EdxnotesVisibilityDecorator.enableNote);
            this.actionLink.addClass('is-active');
            this.label.text(gettext('Hide notes'));
            this.actionToggleMessage.text(gettext('Showing notes'));
        },

        disableNotes: function () {
            EdxnotesVisibilityDecorator.disableNotes();
            this.actionLink.removeClass('is-active');
            this.label.text(gettext('Show notes'));
            this.actionToggleMessage.text(gettext('Hiding notes'));
        },

        hideErrorMessage: function() {
            this.notification.hide();
        },

        showErrorMessage: function(message) {
            this.notification.show(message, Annotator.Notification.ERROR);
        },

        sendRequest: function () {
            return $.ajax({
                type: 'PUT',
                url: this.visibilityUrl,
                dataType: 'json',
                data: JSON.stringify({'visibility': this.visibility}),
                success: this.onSuccess,
                error: this.onError
            });
        },

        onSuccess: function () {
            this.hideErrorMessage();
        },

        onError: function () {
            this.showErrorMessage(this.errorMessage);
        }
    });

    return function (visibility, visibilityUrl) {
        return new ToggleNotesView({
            el: $('.edx-notes-visibility').get(0),
            visibility: visibility,
            visibilityUrl: visibilityUrl
        });
    };
});
}).call(this, define || RequireJS.define);
