define(["jquery", "underscore", "underscore.string", "backbone", "js/utils/templates"],
    function($, _, str, Backbone, TemplateUtils) {
        var SystemFeedback = Backbone.View.extend({
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
                if (!this.options.type) {
                    throw "SystemFeedback: type required (given " +
                        JSON.stringify(this.options) + ")";
                }
                if (!this.options.intent) {
                    throw "SystemFeedback: intent required (given " +
                        JSON.stringify(this.options) + ")";
                }
                this.template = TemplateUtils.loadTemplate("system-feedback");
                this.setElement($("#page-" + this.options.type));
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
                if ($.isNumeric(this.options.maxShown)) {
                    this.hideTimeout = setTimeout(_.bind(this.hide, this),
                        this.options.maxShown);
                }
                return this;
            },

            hide: function() {
                if (this.shownAt && $.isNumeric(this.options.minShown) &&
                        this.options.minShown > new Date() - this.shownAt) {
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
                var singleton = SystemFeedback["active_" + this.options.type];
                if (singleton && singleton !== this) {
                    singleton.stopListening();
                    singleton.undelegateEvents();
                }
                this.$el.html(this.template(this.options));
                SystemFeedback["active_" + this.options.type] = this;
                return this;
            },

            primaryClick: function(event) {
                var actions, primary;
                actions = this.options.actions;
                if (!actions) { return; }
                primary = actions.primary;
                if (!primary) { return; }
                if (primary.preventDefault !== false) {
                    event.preventDefault();
                }
                if (primary.click) {
                    primary.click.call(event.target, this, event);
                }
            },

            secondaryClick: function(event) {
                var actions, secondaryList, secondary, i;
                actions = this.options.actions;
                if (!actions) { return; }
                secondaryList = actions.secondary;
                if (!secondaryList) { return; }
                // which secondary action was clicked?
                i = 0;  // default to the first secondary action (easier for testing)
                if (event && event.target) {
                    i = _.indexOf(this.$(".action-secondary"), event.target);
                }
                secondary = secondaryList[i];
                if (secondary.preventDefault !== false) {
                    event.preventDefault();
                }
                if (secondary.click) {
                    secondary.click.call(event.target, this, event);
                }
            }
        });
        return SystemFeedback;
    });
