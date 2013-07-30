CMS.Views.SystemFeedback = Backbone.View.extend({
    options: {
        title: "",
        message: "",
        intent: null,  // "warning", "confirmation", "error", "announcement", "step-required", etc
        type: null, // "alert", "notification", or "prompt": set by subclass
        shown: true,  // is this view currently being shown?
        icon: true,  // should we render an icon related to the message intent?
        closeIcon: true,  // should we render a close button in the top right corner?
        minShown: 0,  // length of time after this view has been shown before it can be hidden (milliseconds)
        maxShown: Infinity  // length of time after this view has been shown before it will be automatically hidden (milliseconds)

        /* Could also have an "actions" hash: here is an example demonstrating
           the expected structure. For each action, by default the framework
           will call preventDefault on the click event before the function is
           run; to make it not do that, just pass `preventDefault: false` in
           the action object.

        actions: {
            primary: {
                "text": "Save",
                "class": "action-save",
                "click": function(view) {
                    // do something when Save is clicked
                }
            },
            secondary: [
                {
                    "text": "Cancel",
                    "class": "action-cancel",
                    "click": function(view) {}
                }, {
                    "text": "Discard Changes",
                    "class": "action-discard",
                    "click": function(view) {}
                }
            ]
        }
        */
    },
    initialize: function() {
        if(!this.options.type) {
            throw "SystemFeedback: type required (given " +
                JSON.stringify(this.options) + ")";
        }
        if(!this.options.intent) {
            throw "SystemFeedback: intent required (given " +
                JSON.stringify(this.options) + ")";
        }
        var tpl = $("#system-feedback-tpl").text();
        if(!tpl) {
            console.error("Couldn't load system-feedback template");
        }
        this.template = _.template(tpl);
        this.setElement($("#page-"+this.options.type));
        // handle single "secondary" action
        if (this.options.actions && this.options.actions.secondary &&
            !_.isArray(this.options.actions.secondary)) {
            this.options.actions.secondary = [this.options.actions.secondary];
        }
        return this;
    },
    // public API: show() and hide()
    show: function() {
        clearTimeout(this.hideTimeout);
        this.options.shown = true;
        this.shownAt = new Date();
        this.render();
        if($.isNumeric(this.options.maxShown)) {
            this.hideTimeout = setTimeout(_.bind(this.hide, this),
                this.options.maxShown);
        }
        return this;
    },
    hide: function() {
        if(this.shownAt && $.isNumeric(this.options.minShown) &&
           this.options.minShown > new Date() - this.shownAt)
        {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = setTimeout(_.bind(this.hide, this),
                this.options.minShown - (new Date() - this.shownAt));
        } else {
            this.options.shown = false;
            delete this.shownAt;
            this.render();
        }
        return this;
    },
    // the rest of the API should be considered semi-private
    events: {
        "click .action-close": "hide",
        "click .action-primary": "primaryClick",
        "click .action-secondary": "secondaryClick"
    },
    render: function() {
        // there can be only one active view of a given type at a time: only
        // one alert, only one notification, only one prompt. Therefore, we'll
        // use a singleton approach.
        var parent = CMS.Views[_.str.capitalize(this.options.type)];
        if(parent && parent.active && parent.active !== this) {
            parent.active.stopListening();
            parent.active.undelegateEvents();
        }
        this.$el.html(this.template(this.options));
        parent.active = this;
        return this;
    },
    primaryClick: function(event) {
        var actions = this.options.actions;
        if(!actions) { return; }
        var primary = actions.primary;
        if(!primary) { return; }
        if(primary.preventDefault !== false) {
            event.preventDefault();
        }
        if(primary.click) {
            primary.click.call(event.target, this, event);
        }
    },
    secondaryClick: function(event) {
        var actions = this.options.actions;
        if(!actions) { return; }
        var secondaryList = actions.secondary;
        if(!secondaryList) { return; }
        // which secondary action was clicked?
        var i = 0;  // default to the first secondary action (easier for testing)
        if(event && event.target) {
            i = _.indexOf(this.$(".action-secondary"), event.target);
        }
        var secondary = secondaryList[i];
        if(secondary.preventDefault !== false) {
            event.preventDefault();
        }
        if(secondary.click) {
            secondary.click.call(event.target, this, event);
        }
    }
});

CMS.Views.Alert = CMS.Views.SystemFeedback.extend({
    options: $.extend({}, CMS.Views.SystemFeedback.prototype.options, {
        type: "alert"
    }),
    slide_speed: 900,
    show: function() {
        CMS.Views.SystemFeedback.prototype.show.apply(this, arguments);
        this.$el.hide();
        this.$el.slideDown(this.slide_speed);
        return this;
    },
    hide: function () {
        this.$el.slideUp({
            duration: this.slide_speed
        });
        setTimeout(_.bind(CMS.Views.SystemFeedback.prototype.hide, this, arguments),
                   this.slideSpeed);
    }
});
CMS.Views.Notification = CMS.Views.SystemFeedback.extend({
    options: $.extend({}, CMS.Views.SystemFeedback.prototype.options, {
        type: "notification",
        closeIcon: false
    })
});
CMS.Views.Prompt = CMS.Views.SystemFeedback.extend({
    options: $.extend({}, CMS.Views.SystemFeedback.prototype.options, {
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
        return CMS.Views.SystemFeedback.prototype.render.apply(this, arguments);
    }
});

// create CMS.Views.Alert.Warning, CMS.Views.Notification.Confirmation,
// CMS.Views.Prompt.StepRequired, etc
var capitalCamel, types, intents;
capitalCamel = _.compose(_.str.capitalize, _.str.camelize);
types = ["alert", "notification", "prompt"];
intents = ["warning", "error", "confirmation", "announcement", "step-required", "help", "mini"];
_.each(types, function(type) {
    _.each(intents, function(intent) {
        // "class" is a reserved word in Javascript, so use "klass" instead
        var klass, subklass;
        klass = CMS.Views[capitalCamel(type)];
        subklass = klass.extend({
            options: $.extend({}, klass.prototype.options, {
                type: type,
                intent: intent
            })
        });
        klass[capitalCamel(intent)] = subklass;
    });
});

// set more sensible defaults for Notification-Mini views
var miniOptions = CMS.Views.Notification.Mini.prototype.options;
miniOptions.minShown = 1250;
miniOptions.closeIcon = false;
