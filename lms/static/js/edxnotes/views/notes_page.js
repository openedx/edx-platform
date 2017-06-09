(function(define, undefined) {
    'use strict';
    define([
        'backbone', 'js/edxnotes/collections/tabs', 'js/edxnotes/views/tabs_list',
        'js/edxnotes/views/tabs/recent_activity', 'js/edxnotes/views/tabs/course_structure',
        'js/edxnotes/views/tabs/search_results', 'js/edxnotes/views/tabs/tags'
    ], function(
    Backbone, TabsCollection, TabsListView, RecentActivityView, CourseStructureView,
    SearchResultsView, TagsView
) {
        var NotesPageView = Backbone.View.extend({
            initialize: function(options) {
                var scrollToTag, tagsModel;

                this.options = options;
                this.tabsCollection = new TabsCollection();

                if (!_.contains(this.options.disabledTabs, 'tags')) {
                // Must create the Tags view first to get the "scrollToTag" method.
                    this.tagsView = new TagsView({
                        el: this.el,
                        collection: this.collection,
                        tabsCollection: this.tabsCollection
                    });

                    scrollToTag = this.tagsView.scrollToTag;

                // Remove the Tags model from the tabs collection because it should not appear first.
                    tagsModel = this.tabsCollection.shift();
                }

                this.recentActivityView = new RecentActivityView({
                    el: this.el,
                    collection: this.collection,
                    tabsCollection: this.tabsCollection,
                    scrollToTag: scrollToTag
                });

                if (!_.contains(this.options.disabledTabs, 'course_structure')) {
                    this.courseStructureView = new CourseStructureView({
                        el: this.el,
                        collection: this.collection,
                        tabsCollection: this.tabsCollection,
                        scrollToTag: scrollToTag
                    });
                }

                if (!_.contains(this.options.disabledTabs, 'tags')) {
                // Add the Tags model after the Course Structure model.
                    this.tabsCollection.push(tagsModel);
                }

                this.searchResultsView = new SearchResultsView({
                    el: this.el,
                    tabsCollection: this.tabsCollection,
                    debug: this.options.debug,
                    perPage: this.options.perPage,
                    createTabOnInitialization: false,
                    scrollToTag: scrollToTag
                });

                this.tabsView = new TabsListView({collection: this.tabsCollection});
                this.$('.tab-list')
                .append(this.tabsView.render().$el)
                .removeClass('is-hidden');
            }
        });

        return NotesPageView;
    });
}).call(this, define || RequireJS.define);
