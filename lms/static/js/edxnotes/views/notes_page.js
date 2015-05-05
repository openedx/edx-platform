;(function (define, undefined) {
'use strict';
define([
    'backbone', 'js/edxnotes/collections/tabs', 'js/edxnotes/views/tabs_list',
    'js/edxnotes/views/tabs/recent_activity', 'js/edxnotes/views/tabs/course_structure',
    'js/edxnotes/views/tabs/search_results', 'js/edxnotes/views/tabs/tags'
], function (
    Backbone, TabsCollection, TabsListView, RecentActivityView, CourseStructureView,
    SearchResultsView, TagsView
) {
    var NotesPageView = Backbone.View.extend({
        initialize: function (options) {
            this.options = options;
            this.tabsCollection = new TabsCollection();

            this.recentActivityView = new RecentActivityView({
                el: this.el,
                collection: this.collection,
                tabsCollection: this.tabsCollection
            });

            this.courseStructureView = new CourseStructureView({
                el: this.el,
                collection: this.collection,
                tabsCollection: this.tabsCollection
            });

            this.tagsView = new TagsView({
                el: this.el,
                collection: this.collection,
                tabsCollection: this.tabsCollection
            });

            this.searchResultsView = new SearchResultsView({
                el: this.el,
                tabsCollection: this.tabsCollection,
                debug: this.options.debug,
                createTabOnInitialization: false
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
