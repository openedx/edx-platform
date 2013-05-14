CMS.Views.Alert = Backbone.View.extend({
    options: {
        type: "alert",
        shown: true,  // is this view currently being shown?
        closeIcon: true  // should we render a close button in the top right corner?
    },
    initialize: function() {
        this.template = _.template($("#"+this.options.type+"-tpl").text()),
        this.setElement($("#page-"+this.options.type));
        this.listenTo(this.model, 'change', this.render);
        return this.render();
    },
    render: function() {
        var attrs = $.extend({}, this.options, this.model.attributes);
        this.$el.html(this.template(attrs));
        return this;
    },
    events: {
        "click .action-close": "hide",
        "click .action-primary": "primaryClick",
        "click .action-secondary": "secondaryClick"
    },
    show: function() {
        this.options.shown = true;
        return this.render();
    },
    hide: function() {
        this.options.shown = false;
        return this.render();
    },
    primaryClick: function() {
        var actions = this.model.get("actions");
        if(!actions) { return; }
        var primary = actions.primary;
        if(!primary) { return; }
        if(primary.click) {
            primary.click.call(this.model, this);
        }
    },
    secondaryClick: function(e) {
        var actions = this.model.get("actions");
        if(!actions) { return; }
        var secondaryList = actions.secondary;
        if(!secondaryList) { return; }
        // which secondary action was clicked?
        var i;
        if(e && e.target) {
            i = _.indexOf(this.$(".action-secondary"), e.target);
        } else {
            i = 0;
        }
        var secondary = this.model.get("actions").secondary[i];
        if(secondary.click) {
            secondary.click.call(this.model, this);
        }
    }
});

CMS.Views.Notification = CMS.Views.Alert.extend({
    options: $.extend({}, CMS.Views.Alert.prototype.options, {
        type: "notification",
        closeIcon: false
    })
});
CMS.Views.Prompt = CMS.Views.Alert.extend({
    options: $.extend({}, CMS.Views.Alert.prototype.options, {
        type: "prompt",
        closeIcon: false
    }),
    render: function() {
        if(!window.$body) { window.$body = $(document.body); }
        if(this.model.get('shown')) {
            $body.addClass('prompt-is-shown');
        } else {
            $body.removeClass('prompt-is-shown');
        }
        // super() in Javascript has awkward syntax :(
        return CMS.Views.Alert.prototype.render.apply(this, arguments);
    }
});
