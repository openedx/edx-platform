CMS.Views.SystemFeedback = Backbone.View.extend({
    initialize: function() {
        this.setElement($("#page-"+this.type));
        this.listenTo(this.model, 'change', this.render);
        return this.render();
    },
    template: _.template($("#system-feedback-tpl").text()),
    render: function() {
        var attrs = $.extend({}, this.model.attributes);
        if(attrs.type) {
            attrs.modelType = attrs.type;
            delete attrs.type;
        }
        attrs.viewType = this.type;
        this.$el.html(this.template(attrs));
        return this;
    },
    events: {
        "click .action-close": "hide",
        "click .action-primary": "primaryClick",
        "click .action-secondary": "secondaryClick"
    },
    hide: function() {
        this.model.hide();
    },
    primaryClick: function() {
        var actions = this.model.get("actions");
        if(!actions) { return; }
        var primary = actions.primary;
        if(!primary) { return; }
        if(primary.click) {
            primary.click.call(this.model);
        }
    },
    secondaryClick: function(e) {
        var actions = this.model.get("actions");
        if(!actions) { return; }
        var secondaryList = actions.secondary;
        if(!secondaryList) { return; }
        // which secondary action was clicked?
        var i = _.indexOf(this.$(".action-secondary"), e.target);
        var secondary = this.model.get("actions").secondary[i];
        if(secondary.click) {
            secondary.click.call(this.model);
        }
    }
});

CMS.Views.Alert = CMS.Views.SystemFeedback.extend({
    type: "alert"
});
CMS.Views.Notification = CMS.Views.SystemFeedback.extend({
    type: "notification"
});
CMS.Views.Prompt = CMS.Views.SystemFeedback.extend({
    type: "prompt",
    render: function() {
        if(!window.$body) { window.$body = $(document.body); }
        if(this.model.get('shown')) {
            $body.addClass('prompt-is-shown');
        } else {
            $body.removeClass('prompt-is-shown');
        }
        // super() in Javascript has awkward syntax :(
        return CMS.Views.SystemFeedback.prototype.render.apply(this, arguments);
    }
});
