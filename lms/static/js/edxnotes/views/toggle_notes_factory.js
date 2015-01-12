;(function (define, undefined) {
'use strict';
define([
    'jquery', 'underscore', 'backbone', 'gettext',
    'annotator', 'js/edxnotes/views/visibility_decorator'
], function($, _, Backbone, gettext, Annotator, EdxnotesVisibilityDecorator) {
    var ToggleNotesView = Backbone.View.extend({
        events: {
            'click .action-toggle-notes': 'toogleHandler'
        },

        errorMessage: gettext("An error has occurred. Make sure that you are connected to the Internet, and then try refreshing the page."),

        initialize: function (options) {
            this.visibility = options.visibility;
            this.visibilityUrl = options.visibilityUrl;
            this.label = this.$('.utility-control-label');
            this.actionLink = this.$('.action-toggle-notes');
            this.actionLink.removeClass('is-disabled');
            this.notification = new Annotator.Notification();
        },

        toogleHandler: function (event) {
            event.preventDefault();
            this.visibility = !this.visibility;
            this.toggleNotes();
            this.sendRequest();
        },

        toggleNotes: function () {
            if (this.visibility) {
                _.each($('.edx-notes-wrapper'), EdxnotesVisibilityDecorator.enableNote);
                this.actionLink.addClass('is-active').attr('aria-pressed', true);
                this.label.text(gettext('Hide notes'));
            } else {
                EdxnotesVisibilityDecorator.disableNotes();
                this.actionLink.removeClass('is-active').attr('aria-pressed', false);
                this.label.text(gettext('Show notes'));
            }
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
                success: _.bind(this.onSuccess, this),
                error: _.bind(this.onError, this)
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
