var NotificationPreferencesView = Backbone.View.extend({
    initialize: function (options) {
        this.global_variables = options.global_variables;

        /* get out main underscore view template */
        this.template = _.template($('#xns-notification-preferences-template').html());

        // set up our URLs for the API
        this.notification_preferences_all = options.endpoints.notification_preferences_all;
        this.user_notification_preferences = options.endpoints.user_notification_preferences;
        this.user_notification_preferences_detail = options.endpoints.user_notification_preferences_detail;


        /* set up our collection */
        this.collection = new NotificationPreferencesCollection();

        /* set the API endpoint that was passed into our initializer */
        this.collection.url = this.notification_preferences_all;

        /* re-render if the model changes */
        this.listenTo(this.collection, 'change', this.collectionChanged);

        this.hydrate();
    },

    events: {
        'click .xns-preference': 'changeUserPreference'
    },
    getCSRFToken: function() {
        var cookieValue = null;
        var name='csrftoken';
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },
    changeUserPreference: function(e){
        /* update the user preferences */
        var value = e.currentTarget.checked;
        var preference_name = $(e.currentTarget).data('preference-name');
        var self = this;
        self.collection.url = this.user_notification_preferences_detail + preference_name;
        self.collection.fetch(
            {
                headers: {
                    "X-CSRFToken": this.getCSRFToken()
                },
                type: 'POST',
                data: {'value': value},
                success: function () {
                    // fetch the user preferences again.
                    self.collection.url = self.notification_preferences_all;
                    self.hydrate();
                }
            }
        );
        e.stopPropagation();
        e.preventDefault();
    },
    collectionChanged: function() {
        /* redraw for now */
        this.render();
    },
    hydrate: function() {
        /* This function will load the bound collection */

        /* add and remove a class when we do the initial loading */
        /* we might - at some point - add a visual element to the */
        /* loading, like a spinner */
        var self = this;
        this.collection.fetch({
            success: function(){
                self.render();
            }
        });
    },
    render: function(){
        /* update the user preferences */
        var notification_preferences = this.collection.toJSON();
        this.checkForExplicitOverrides(notification_preferences);
    },
    checkForExplicitOverrides: function(notification_preferences){
        /* check the user preferences */
        var self = this;
        self.collection.url = self.user_notification_preferences;
        self.collection.fetch({
            success: function(){
                var user_preferences = self.collection.toJSON();
                $.each(user_preferences, function(i) {
                    $.each(notification_preferences, function(j) {
                        if (notification_preferences[j].name == user_preferences[i].preference.name) {
                            notification_preferences[j]['user_value'] = user_preferences[i].value;
                        }
                    });
                });
                // render the user preferences.
                var _html = self.template({'notification_preferences': notification_preferences});
                self.$el.html(_html);
            }
        });
    },
    showFetchedPreferences: function(el){
        /* render the notification pane html with
        * with the notification preferences tab view
        * */
        el.html(this.$el);
    }
});
