(function(define) {
    'use strict';
    define(['jquery',
            'underscore',
            'underscore.string',
            'backbone',
            'text!common/templates/components/system-feedback.underscore'],
        function($, _, str, Backbone, systemFeedbackTemplate) {
            var tabbable_elements = [
                "a[href]:not([tabindex='-1'])",
                "area[href]:not([tabindex='-1'])",
                "input:not([disabled]):not([tabindex='-1'])",
                "select:not([disabled]):not([tabindex='-1'])",
                "textarea:not([disabled]):not([tabindex='-1'])",
                "button:not([disabled]):not([tabindex='-1'])",
                "iframe:not([tabindex='-1'])",
                "[tabindex]:not([tabindex='-1'])",
                "[contentEditable=true]:not([tabindex='-1'])"
            ];
            var SystemFeedback = Backbone.View.extend({
                options: {
                    title: '',
                    message: '',
                    intent: null,  // "warning", "confirmation", "error", "announcement", "step-required", etc
                    type: null, // "alert", "notification", or "prompt": set by subclass
                    shown: true,  // is this view currently being shown?
                    icon: true,  // should we render an icon related to the message intent?
                    closeIcon: true,  // should we render a close button in the top right corner?
                    minShown: 0,  // length of time after this view has been shown before it can be hidden (milliseconds)
                    maxShown: Infinity,  // length of time after this view has been shown before it will be automatically hidden (milliseconds)
                    outFocusElement: null  // element to send focus to on hide

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

                initialize: function(options) {
                    this.options = _.extend({}, this.options, options);
                    if (!this.options.type) {
                        throw 'SystemFeedback: type required (given ' +
                            JSON.stringify(this.options) + ')';
                    }
                    if (!this.options.intent) {
                        throw 'SystemFeedback: intent required (given ' +
                            JSON.stringify(this.options) + ')';
                    }
                    this.setElement($('#page-' + this.options.type));
                    // handle single "secondary" action
                    if (this.options.actions && this.options.actions.secondary &&
                            !_.isArray(this.options.actions.secondary)) {
                        this.options.actions.secondary = [this.options.actions.secondary];
                    }
                    return this;
                },

                inFocus: function() {
                    this.options.outFocusElement = this.options.outFocusElement || document.activeElement;

                    // Set focus to the container.
                    this.$('.wrapper').first().focus();


                    // Make tabs within the prompt loop rather than setting focus
                    // back to the main content of the page.
                    var tabbables = this.$(tabbable_elements.join());
                    tabbables.on('keydown', function(event) {
                        // On tab backward from the first tabbable item in the prompt
                        if (event.which === 9 && event.shiftKey && event.target === tabbables.first()[0]) {
                            event.preventDefault();
                            tabbables.last().focus();
                        }
                        // On tab forward from the last tabbable item in the prompt
                        else if (event.which === 9 && !event.shiftKey && event.target === tabbables.last()[0]) {
                            event.preventDefault();
                            tabbables.first().focus();
                        }
                    });

                    return this;
                },

                outFocus: function() {
                    var tabbables = this.$(tabbable_elements.join()).off('keydown');
                    if (this.options.outFocusElement) {
                        this.options.outFocusElement.focus();
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
                    'click .action-close': 'hide',
                    'click .action-primary': 'primaryClick',
                    'click .action-secondary': 'secondaryClick'
                },

                render: function() {
                    // there can be only one active view of a given type at a time: only
                    // one alert, only one notification, only one prompt. Therefore, we'll
                    // use a singleton approach.
                    var singleton = SystemFeedback['active_' + this.options.type];
                    if (singleton && singleton !== this) {
                        singleton.stopListening();
                        singleton.undelegateEvents();
                    }
                    this.$el.html(_.template(systemFeedbackTemplate)(this.options));
                    SystemFeedback['active_' + this.options.type] = this;
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
                        i = _.indexOf(this.$('.action-secondary'), event.target);
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
}).call(this, define || RequireJS.define);
