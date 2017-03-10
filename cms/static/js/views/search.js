(function(define) { 
    'use strict';

    define([
        'underscore',
        'backbone',
        'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/constants',
        'text!templates/search.underscore'
    ],
    function(_, Backbone, HtmlUtils, constants, searchTemplate) {
        /*
         * TODO: Much of the actual search functionality still takes place in discussion_thread_list_view.js
         * Because of how it's structured there, extracting it is a massive task. Significant refactoring is needed
         * in order to clean up that file and make it possible to break its logic into files like this one.
         */
        var searchView = Backbone.View.extend({
            events: {
<<<<<<< cac68c7cb170e74479b89dc43811b9cec2834b7a
                    'click .search-button': 'searchKey',
                    'click .cancel-button': 'cancelSearch'
=======
                    'click .search-btn': 'searchKey',
>>>>>>> [WIP] Add search box to video page
            },

            initialize: function(options) {
                this.template = HtmlUtils.template(searchTemplate);
<<<<<<< cac68c7cb170e74479b89dc43811b9cec2834b7a
                this.render();
=======
>>>>>>> [WIP] Add search box to video page
            },

            render: function() {
                HtmlUtils.setHtml(this.$el, this.template());
<<<<<<< cac68c7cb170e74479b89dc43811b9cec2834b7a
                this.$searchField = this.$el.find('.search-field');
                this.$searchButton = this.$el.find('.search-button');
                this.$cancelButton = this.$el.find('.cancel-button');
=======
>>>>>>> [WIP] Add search box to video page
                return this;
            },

            searchKey: function() {
<<<<<<< cac68c7cb170e74479b89dc43811b9cec2834b7a
                var searchKey = this.$('.search-field').val();
                this.collection.setSearchKey(searchKey);
                this.collection.setPage(1);
                this.$searchField.addClass('is-active');
                this.$searchButton.hide();
                this.$cancelButton.show();
            },

            cancelSearch: function() {
                this.$('.search-field').val('');
                this.collection.setSearchKey('');
                this.collection.setPage(1);
                this.$searchField.removeClass('is-active');
                this.$searchButton.show();
                this.$cancelButton.hide();
=======
                var searchKey = this.$('.search-input').val();
                this.collection.setSearchKey(searchKey);
                this.collection.setPage(1);
                searchKey.val('');
>>>>>>> [WIP] Add search box to video page
            }
        });

        return searchView;
    });
}).call(this, define || RequireJS.define);