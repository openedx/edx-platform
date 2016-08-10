(function(define) {
    'use strict';

    define([
        'underscore',
        'backbone',
        'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/constants',
        'text!discussion/templates/search.underscore'
    ],
    function(_, Backbone, HtmlUtils, constants, searchTemplate) {
        /*
         * TODO: Much of the actual search functionality still takes place in discussion_thread_list_view.js
         * Because of how it's structured there, extracting it is a massive task. Significant refactoring is needed
         * in order to clean up that file and make it possible to break its logic into files like this one.
         */
        var searchView = Backbone.View.extend({
            events: {
                'keydown .search-input': 'performSearch',
                'click .search-btn': 'performSearch',
                'topic:selected': 'clearSearch'
            },
            initialize: function(options) {
                _.extend(this, _.pick(options, 'threadListView'));

                this.template = HtmlUtils.template(searchTemplate);
                this.threadListView = options.threadListView;

                this.listenTo(this.model, 'change', this.render);
                this.render();
            },
            render: function() {
                HtmlUtils.setHtml(this.$el, this.template());
                return this;
            },
            performSearch: function(event) {
                if (event.which === constants.keyCodes.enter || event.type === 'click') {
                    event.preventDefault();
                    this.threadListView.performSearch($('.search-input', this.$el));
                }
            },
            clearSearch: function() {
                this.$('.search-input').val('');
                this.threadListView.clearSearchAlerts();
            }
        });

        return searchView;
    });
}).call(this, define || RequireJS.define);
