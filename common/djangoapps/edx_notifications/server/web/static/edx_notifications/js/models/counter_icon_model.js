var CounterIconModel = Backbone.Model.extend({
    /* model for the Notification Icon which will display a counter of unread messages */
    defaults: {
        /* start with unknown number of unread notifications */
        'count': null
    }
});
