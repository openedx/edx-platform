CMS.Views.Alert = Backbone.View.extend({
    options: {
        type: "alert",
        shown: true,  // is this view currently being shown?
        icon: true,  // should we render an icon related to the message intent?
        closeIcon: true,  // should we render a close button in the top right corner?
        minShown: 0,  // length of time after this view has been shown before it can be hidden (milliseconds)
        maxShown: Infinity  // length of time after this view has been shown before it will be automatically hidden (milliseconds)
    },
    initialize: function() {
        var tpl = $("#system-feedback-tpl").text();
        if(!tpl) {
            console.error("Couldn't load system-feedback template");
        }
        this.template = _.template(tpl);
        this.setElement($("#page-"+this.options.type));
        this.listenTo(this.model, 'change', this.render);
        return this.show();
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
        clearTimeout(this.hideTimeout);
        this.options.shown = true;
        this.shownAt = new Date();
        this.render();
        if($.isNumeric(this.options.maxShown)) {
            this.hideTimeout = setTimeout($.proxy(this.hide, this),
                this.options.maxShown);
        }
        return this;
    },
    hide: function() {
        if(this.shownAt && $.isNumeric(this.options.minShown) &&
           this.options.minShown > new Date() - this.shownAt)
        {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = setTimeout($.proxy(this.hide, this),
                this.options.minShown - (new Date() - this.shownAt));
        } else {
            this.options.shown = false;
            delete this.shownAt;
            this.render();
        }
        return this;
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
        var i = 0;  // default to the first secondary action (easier for testing)
        if(e && e.target) {
            i = _.indexOf(this.$(".action-secondary"), e.target);
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
        closeIcon: false,
        icon: false
    }),
    render: function() {
        if(!window.$body) { window.$body = $(document.body); }
        if(this.options.shown) {
            $body.addClass('prompt-is-shown');
        } else {
            $body.removeClass('prompt-is-shown');
        }
        // super() in Javascript has awkward syntax :(
        return CMS.Views.Alert.prototype.render.apply(this, arguments);
    }
});
