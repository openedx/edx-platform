;(function (define) {
    'use strict';
    define(['backbone',
            'underscore',
            'jquery',
            'text!common/templates/components/tabbed_view.underscore',
            'text!common/templates/components/tab.underscore',
            'text!common/templates/components/tabpanel.underscore',
           ], function (
               Backbone,
               _,
               $,
               tabbedViewTemplate,
               tabTemplate,
               tabPanelTemplate
           ) {
               var getTabPanelId = function (id) {
                   return 'tabpanel-' + id;
               };

               var TabPanelView = Backbone.View.extend({
                   template: _.template(tabPanelTemplate),
                   initialize: function (options) {
                       this.url = options.url;
                       this.view = options.view;
                   },
                   render: function () {
                       var tabPanelHtml = this.template({tabId: getTabPanelId(this.url)});
                       this.setElement($(tabPanelHtml));
                       this.$el.append(this.view.render().el);
                       return this;
                   }
               });

               var TabbedView = Backbone.View.extend({
                   events: {
                       'click .nav-item.tab': 'switchTab'
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
                   initialize: function (options) {
                       this.router = options.router || null;
                       this.tabs = options.tabs;
                       this.template = _.template(tabbedViewTemplate)({viewLabel: options.viewLabel});
                       // Convert each view into a TabPanelView
                       _.each(this.tabs, function (tabInfo) {
                           tabInfo.view = new TabPanelView({url: tabInfo.url, view: tabInfo.view});
                       }, this);
                       this.urlMap = _.reduce(this.tabs, function (map, value) {
                           map[value.url] = value;
                           return map;
                       }, {});
                   },

                   render: function () {
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

                   setActiveTab: function (index) {
                       var tabMeta = this.getTabMeta(index),
                           tab = tabMeta.tab,
                           tabEl = tabMeta.element,
                           view = tab.view;
                       // Hide old tab/tabpanel
                       this.$('button.is-active').removeClass('is-active').attr('aria-expanded', 'false');
                       this.$('.tabpanel[aria-expanded="true"]').attr('aria-expanded', 'false').addClass('is-hidden');
                       // Show new tab/tabpanel
                       tabEl.addClass('is-active').attr('aria-expanded', 'true');
                       view.$el.attr('aria-expanded', 'true').removeClass('is-hidden');
                       // This bizarre workaround makes focus work in Chrome.
                       _.defer(function () {
                           view.$('.sr-is-focusable.' + getTabPanelId(tab.url)).focus();
                       });
                       if (this.router) {
                           this.router.navigate(tab.url, {replace: true});
                       }
                   },

                   switchTab: function (event) {
                       event.preventDefault();
                       this.setActiveTab($(event.currentTarget).data('index'));
                   },

                   /**
                    * Get the tab by name or index. Returns an object
                    * encapsulating the tab object and its element.
                    */
                   getTabMeta: function (tabNameOrIndex) {
                       var tab, element;
                       if (typeof tabNameOrIndex === 'string') {
                           tab = this.urlMap[tabNameOrIndex];
                           element = this.$('button[data-url='+tabNameOrIndex+']');
                       }  else {
                           tab = this.tabs[tabNameOrIndex];
                           element = this.$('button[data-index='+tabNameOrIndex+']');
                       }
                       return {'tab': tab, 'element': element};
                   }
               });
               return TabbedView;
           });
}).call(this, define || RequireJS.define);
