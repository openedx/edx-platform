/**
 * A search field that works in concert with a paginated collection. When the user
 * performs a search, the collection's search string will be updated and then the
 * collection will be refreshed to show the first page of results.
 */
(function(define) {
    'use strict';

    define([
        'backbone',
        'jquery',
        'underscore',
        'edx-ui-toolkit/js/utils/html-utils',
        'text!common/templates/components/search-field.underscore'
    ],
        function(Backbone, $, _, HtmlUtils, searchFieldTemplate) {
            return Backbone.View.extend({

                events: {
                    'submit .search-form': 'performSearch',
                    'blur .search-form': 'onFocusOut',
                    'keyup .search-field': 'refreshState',
                    'click .action-clear': 'clearSearch',
                    'mouseover .action-clear': 'setMouseOverState',
                    'mouseout .action-clear': 'setMouseOutState'
                },

                initialize: function(options) {
                    this.type = options.type;
                    this.label = options.label;
                    this.mouseOverClear = false;
                },

                refreshState: function() {
                    var searchField = this.$('.search-field'),
                        clearButton = this.$('.action-clear'),
                        searchString = $.trim(searchField.val());

                    if (searchString) {
                        clearButton.removeClass('is-hidden');
                    } else {
                        clearButton.addClass('is-hidden');
                    }
                },

                render: function() {
                    HtmlUtils.setHtml(
                        this.$el,
                        HtmlUtils.template(searchFieldTemplate)({
                            type: this.type,
                            searchString: this.collection.searchString,
                            searchLabel: this.label
                        })
                    );
                    this.refreshState();
                    return this;
                },

                setMouseOverState: function(event) {
                    this.mouseOverClear = true;
                },

                setMouseOutState: function(event) {
                    this.mouseOverClear = false;
                },

                onFocusOut: function(event) {
                    // If the focus is going anywhere but the clear search
                    // button then treat it as a request to search.
                    if (!this.mouseOverClear) {
                        this.performSearch(event);
                    }
                },

                performSearch: function(event) {
                    var searchField = this.$('.search-field'),
                        searchString = $.trim(searchField.val());
                    event.preventDefault();
                    this.collection.setSearchString(searchString);
                    return this.collection.refresh();
                },

                clearSearch: function(event) {
                    event.preventDefault();
                    this.$('.search-field').val('');
                    this.collection.setSearchString('');
                    this.refreshState();
                    return this.collection.refresh();
                }
            });
        });
}).call(this, define || RequireJS.define);
