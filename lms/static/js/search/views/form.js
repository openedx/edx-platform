var edx = edx || {};

(function ($, Backbone) {
   'use strict'

    edx.search = edx.search || {};

    edx.search.Form = Backbone.View.extend({
        el: '#courseware-search',
        events: {
            'submit form': 'submitForm',
            'click .cancel-button': 'clearSearch',
        },
        emptySearchRegex: /^\s*$/,

        initialize: function (options) {
            this.$searchField = this.$el.find('.search-field');
            this.$searchButton = this.$el.find('.search-button');
            this.$cancelButton = this.$el.find('.cancel-button');
        },

        submitForm: function () {
            var searchTerm = this.$searchField.val();
            if (this.emptySearchRegex.test(searchTerm) == false) {
                this.performSearch(searchTerm);
            }
            else {
                this.clearSearch();
            }
            // prevent reload
            return false;
        },

        setActiveStyle: function () {
            this.$searchField.addClass('is-active');
            this.$searchButton.hide();
            this.$cancelButton.show();
        },

        setInitialStyle: function () {
            this.$searchField.removeClass('is-active');
            this.$searchButton.show();
            this.$cancelButton.hide();
        },

        performSearch: function (searchTerm) {
            this.setActiveStyle();
            this.trigger('search', searchTerm);
        },

        clearSearch: function () {
            this.$searchField.val('');
            this.setInitialStyle();
            this.trigger('clear');
        }

    });

})(jQuery, Backbone);
