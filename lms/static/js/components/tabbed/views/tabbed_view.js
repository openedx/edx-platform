;(function (define) {
    'use strict';
    define(['backbone',
            'underscore',
            'jquery',
            'text!templates/components/tabbed/tabbed_view.underscore',
            'text!templates/components/tabbed/tab.underscore'],
           function (Backbone, _, $, tabbedViewTemplate, tabTemplate) {
               var TabbedView = Backbone.View.extend({
                   events: {
                       'click .nav-item[role="tab"]': 'switchTab'
                   },

                   template: _.template(tabbedViewTemplate),

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
                    * by the router's instatiator after this view is
                    * initialized.
                    */
                   initialize: function (options) {
                       var self = this;
                       this.router = options.router || null;
                       this.tabs = options.tabs;
                       if (this.router) {
                           _.each(this.tabs, function(tabInfo, index) {
                               self.router.route(tabInfo.url, function () {
                                   self.setActiveTab(index);
                               });
                           });
                       }
                   },

                   render: function () {
                       var self = this;
                       this.$el.html(this.template({}));
                       _.each(this.tabs, function(tabInfo, index) {
                           var tabEl = $(_.template(tabTemplate, {
                               index: index,
                               title: tabInfo.title
                           }));
                           self.$('.page-content-nav').append(tabEl);
                       });
                       if(Backbone.history.getHash() === "") {
                           this.setActiveTab(0);
                       }
                       return this;
                   },

                   setActiveTab: function (index) {
                       var tab = this.tabs[index],
                           view = tab.view;
                       this.$('a.is-active').removeClass('is-active').attr('aria-selected', 'false');
                       this.$('a[data-index='+index+']').addClass('is-active').attr('aria-selected', 'true');
                       view.setElement(this.$('.page-content-main')).render();
                       this.$('.sr-is-focusable.sr-tab').focus();
                       if (this.router) {
                           this.router.navigate(tab.url, {replace: true});
                       }
                   },

                   switchTab: function (event) {
                       event.preventDefault();
                       this.setActiveTab($(event.currentTarget).data('index'));
                   }
               });
               return TabbedView;
           });
}).call(this, define || RequireJS.define);
