(function(Backbone, $, _) {
    var NotificationView = Backbone.View.extend({
        events : {
            "click .action-primary": "triggerCallback"
        },

        initialize: function() {
            this.template = _.template($('#notification-tpl').text());
        },

        render: function() {
            this.$el.html(this.template({
                type: this.model.get("type"),
                title: this.model.get("title"),
                message: this.model.get("message"),
                details: this.model.get("details"),
                actionText: this.model.get("actionText"),
                actionClass: this.model.get("actionClass"),
                actionIconClass: this.model.get("actionIconClass")
            }));
            this.$('.message').focus();
            return this;
        },

        triggerCallback: function(event) {
            event.preventDefault();
            var actionCallback = this.model.get("actionCallback");
            if (actionCallback) {
                actionCallback(this);
            }
        }
    });

    this.NotificationView = NotificationView;
}).call(this, Backbone, $, _);
