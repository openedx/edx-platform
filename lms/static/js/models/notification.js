(function(Backbone) {
    var NotificationModel = Backbone.Model.extend({
        defaults: {
            // Supported types are "confirmation" and "error".
            type: "confirmation",
            title: "",
            details: [],
            actionText: "",
            actionCallback: null
        }
    });

    this.NotificationModel = NotificationModel;
}).call(this, Backbone);

