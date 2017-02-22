(function(define) {
    'use strict';

    define([
        'backbone',
        'underscore',
        'jquery',
        'edx-ui-toolkit/js/utils/constants',
        'text!common/templates/components/tabbed_view.underscore',
        'text!common/templates/components/tab.underscore',
        'text!common/templates/components/tabpanel.underscore'
    ], function(
        Backbone,
        _,
        $,
        Constants,
        tabbedViewTemplate,
        tabTemplate,
        tabPanelTemplate
    ) {
        var getTabPanelId = function(id) {
            return 'tabpanel-' + id;
        };

        var TabPanelView = Backbone.View.extend({
            template: _.template(tabPanelTemplate),
            initialize: function(options) {
                this.url = options.url;
                this.view = options.view;
                this.index = options.index;
            },
            render: function() {
                var tabPanelHtml = this.template({
                    tabId: getTabPanelId(this.url),
                    index: this.index
                });
                this.setElement($(tabPanelHtml));
                this.$el.append(this.view.render().el);
                return this;
            }
        });

        var TabbedView = Backbone.View.extend({
            events: {
                'click .tab': 'switchTab',
                'keydown .tab': 'keydownHandler'
            },

            /**
            * View for a tabbed interface. Expects a list of tabs
            * in its options object, each of which should contain the
            * following properties:
            *   view (Backbone.View): the view to render for this tab.
            *   title (string): The title to display for this tab.
            *   url (string): The URL fragment which will
            *     navigate to this tab when a router is
            *     provided.
            * If a router is passed in (via options.router),
            * use that router to keep track of history between
            * tabs.  Backbone.history.start() must be called
            * by the router's instantiator after this view is
            * initialized.
            */
            initialize: function(options) {
                this.router = options.router || null;
                this.tabs = options.tabs;
                this.template = _.template(tabbedViewTemplate)({
                    viewLabel: this.viewLabel
                });
                // Convert each view into a TabPanelView
                _.each(this.tabs, function(tabInfo, index) {
                    tabInfo.view = new TabPanelView({
                        url: tabInfo.url,
                        view: tabInfo.view,
                        index: index
                    });
                }, this);
                this.urlMap = _.reduce(this.tabs, function(map, value) {
                    map[value.url] = value;
                    return map;
                }, {});
            },
            render: function() {
                var self = this;
                this.$el.html(this.template);
                _.each(this.tabs, function(tabInfo, index) {
                    var tabEl = $(_.template(tabTemplate)({
                            index: index,
                            title: tabInfo.title,
                            url: tabInfo.url,
                            tabPanelId: getTabPanelId(tabInfo.url)
                        })),
                        tabContainerEl = this.$('.tabs');
                    self.$('.page-content-nav').append(tabEl);

                    // Render and append the current tab panel
                    tabContainerEl.append(tabInfo.view.render().$el);
                }, this);
                // Re-display the default (first) tab if the
                // current route does not belong to one of the
                // tabs.  Otherwise continue displaying the tab
                // corresponding to the current URL.
                if (!(Backbone.history.getHash() in this.urlMap)) {
                    this.setActiveTab(0);
                }

                return this;
            },

            setActiveTab: function(index) {
                var tabMeta = this.getTabMeta(index),
                    tab = tabMeta.tab,
                    view = tab.view,
                    $tabEl = tabMeta.element;

                // Hide old tab/tabpanel
                this.$('button.is-active')
                    .removeClass('is-active')
                    .attr({
                        'aria-expanded': 'false',
                        'aria-selected': 'false',
                        'tabindex': '-1'
                    });

                this.$('.tabpanel[aria-hidden="false"]')
                    .addClass('is-hidden')
                    .attr({
                        'aria-hidden': 'true'
                    });

                // Show new tab/tabpanel
                if (this.router) {
                    this.router.navigate(tab.url, {replace: true});
                }

                $tabEl
                    .addClass('is-active')
                    .attr({
                        'aria-expanded': 'true',
                        'aria-selected': 'true',
                        'tabindex': '0'
                    });

                view.$el
                    .removeClass('is-hidden')
                    .attr({
                        'aria-hidden': 'false'
                    });
            },

            switchTab: function(event) {
                event.preventDefault();
                this.setActiveTab($(event.currentTarget).data('index'));
            },

            previousTab: function(focused, index) {
                var $tab, $panel;

                if (index === 0) {
                    $tab = $(focused).parent().find('.tab').last();
                } else {
                    $tab = $(focused).parent().find('.tab:eq(' + index + ')').prev();
                }

                $panel = $($tab).data('index');

                $tab.focus();

                return false;
            },

            nextTab: function(focused, index, total) {
                var $tab, $panel;

                if (index === total) {
                    $tab = $(focused).parent().find('.tab').first();
                } else {
                    $tab = $(focused).parent().find('.tab:eq(' + index + ')').next();
                }

                $panel = $($tab).data('index');

                $tab.focus();

                return false;
            },

            keydownHandler: function(event) {
                var key = event.which,
                    focused = $(event.currentTarget),
                    index = $(focused).parent().find('.tab').index(focused),
                    total = $(focused).parent().find('.tab').size() - 1,
                    $tab = $(focused).data('index');

                switch (key) {
                case Constants.keyCodes.left:
                case Constants.keyCodes.up:
                    event.preventDefault();
                    this.previousTab(focused, index);
                    break;

                case Constants.keyCodes.right:
                case Constants.keyCodes.down:
                    event.preventDefault();
                    this.nextTab(focused, index, total);
                    break;

                case Constants.keyCodes.enter:
                case Constants.keyCodes.space:
                    this.setActiveTab($tab);
                    break;

                default:
                    return true;
                }
            },

            /**
            * Get the tab by name or index. Returns an object
            * encapsulating the tab object and its element.
            */
            getTabMeta: function(tabNameOrIndex) {
                var tab, $element;

                if (typeof tabNameOrIndex === 'string') {
                    tab = this.urlMap[tabNameOrIndex];
                    $element = this.$('button[data-url=' + tabNameOrIndex + ']');
                } else {
                    tab = this.tabs[tabNameOrIndex];
                    $element = this.$('button[data-index=' + tabNameOrIndex + ']');
                }
                return {'tab': tab, 'element': $element};
            }
        });
        return TabbedView;
    });
}).call(this, define || RequireJS.define);
