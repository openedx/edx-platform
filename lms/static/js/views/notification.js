(function(Backbone, $, _) {
    // eslint-disable-next-line no-var
    var NotificationView = Backbone.View.extend({
        events: {
            'click .action-primary': 'triggerCallback'
        },

        initialize: function() {
            this.template = _.template($('#notification-tpl').text());
        },

        render: function() {
            this.$el.html(this.template({ // xss-lint: disable=javascript-jquery-html
                type: this.model.get('type'),
                title: this.model.get('title'),
                message: this.model.get('message'),
                details: this.model.get('details'),
                actionText: this.model.get('actionText'),
                actionClass: this.model.get('actionClass'),
                actionIconClass: this.model.get('actionIconClass')
            }));
            this.$('.message').focus();
            return this;
        },

        triggerCallback: function(event) {
            event.preventDefault();
            // eslint-disable-next-line no-var
            var actionCallback = this.model.get('actionCallback');
            if (actionCallback) {
                actionCallback(this);
            }
        }
    });

    this.NotificationView = NotificationView;
// eslint-disable-next-line no-undef
}).call(this, Backbone, $, _);
