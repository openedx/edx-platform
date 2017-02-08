(function(Backbone) {
    var NotificationModel = Backbone.Model.extend({
        defaults: {
            /**
             * The type of notification to be shown.
             * Supported types are "confirmation", "warning" and "error".
             */
            type: 'confirmation',
            /**
             * The title to be shown for the notification. This string should be short so
             * that it can be shown on a single line.
             */
            title: '',
            /**
             * An optional message giving more details for the notification. This string can be as long
             * as needed and will wrap.
             */
            message: '',
            /**
             * An optional array of detail messages to be shown beneath the title and message. This is
             * typically used to enumerate a set of warning or error conditions that occurred.
             */
            details: [],
            /**
             * The text label to be shown for an action button, or null if there is no associated action.
             */
            actionText: null,
            /**
             * The class to be added to the action button. This allows selectors to be written that can
             * target the action button directly.
             */
            actionClass: '',
            /**
             * An optional icon class to be shown before the text on the action button.
             */
            actionIconClass: '',
            /**
             * An optional callback that will be invoked when the user clicks on the action button.
             */
            actionCallback: null
        }
    });

    this.NotificationModel = NotificationModel;
}).call(this, Backbone);

