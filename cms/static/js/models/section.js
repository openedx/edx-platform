CMS.Models.Section = Backbone.Model.extend({
    defaults: {
        "name": ""
    },
    validate: function(attrs, options) {
        if (!attrs.name) {
            return gettext("You must specify a name");
        }
    },
    url: "/save_item",
    toJSON: function() {
        return {
            id: this.get("id"),
            metadata: {
                display_name: this.get("name")
            }
        };
    },
    initialize: function() {
        this.listenTo(this, "request", this.showNotification);
        this.listenTo(this, "sync", this.hideNotification);
    },
    showNotification: function() {
        if(!this.msg) {
            this.msg = new CMS.Models.SystemFeedback({
                intent: "saving",
                title: gettext("Saving&hellip;")
            });
        }
        if(!this.msgView) {
            this.msgView = new CMS.Views.Notification({
                model: this.msg,
                closeIcon: false,
                minShown: 1250
            });
        }
        this.msgView.show();
    },
    hideNotification: function() {
        if(!this.msgView) { return; }
        this.msgView.hide();
    }
});
