CMS.Views.SystemFeedback = Backbone.View.extend({
    initialize: function() {
        this.setElement(document.getElementById(this.id));
        this.listenTo(this.model, 'change', this.render);
        return this.render();
    },
    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    },
    events: {
        "click .action-alert-close": "hide",
        "click .action-primary": "primaryClick",
        "click .action-secondary": "secondaryClick"
    },
    hide: function() {
        this.model.set("shown", false);
    },
    primaryClick: function() {
        var primary = this.model.get("actions").primary;
        if(primary.click) {
            primary.click(this.model);
        }
    },
    secondaryClick: function(e) {
        var secondaryList = this.model.get("actions").secondary;
        if(!secondaryList) {
            return;
        }
        // which secondary action was clicked?
        var i = _.indexOf(this.$(".action-secondary"), e.target);
        var secondary = this.model.get("actions").secondary[i];
        if(secondary.click) {
            secondary.click(this.model);
        }
    }
});

CMS.Views.Alert = CMS.Views.SystemFeedback.extend({
    template: _.template($("#alert-tpl").text()),
    id: "page-alert"
});
