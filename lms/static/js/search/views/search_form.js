;(function (define) {

define(['jquery', 'backbone'], function ($, Backbone) {
   'use strict';

    return Backbone.View.extend({

        el: '#courseware-search-bar',
        events: {
            'submit form': 'submitForm',
            'click .cancel-button': 'clearSearch',
        },

        initialize: function () {
            this.$searchField = this.$el.find('.search-field');
            this.$searchButton = this.$el.find('.search-button');
            this.$cancelButton = this.$el.find('.cancel-button');
        },

        submitForm: function (event) {
            event.preventDefault();
            this.doSearch();
        },

        doSearch: function (term) {
            if (term) {
                this.$searchField.val(term);
            }
            else {
                term = this.$searchField.val();
            }

            var trimmed = $.trim(term);
            if (trimmed) {
                this.setActiveStyle();
                this.trigger('search', trimmed);
            }
            else {
                this.clearSearch();
            }
        },

        clearSearch: function () {
            this.$searchField.val('');
            this.setInitialStyle();
            this.trigger('clear');
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
        }

    });

});

})(define || RequireJS.define);
