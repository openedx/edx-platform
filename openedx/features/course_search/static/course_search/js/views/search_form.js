(function(define) {
    'use strict';

    define(['jquery', 'backbone'], function($, Backbone) {
        return Backbone.View.extend({

            el: '',
            events: {
                'submit form': 'submitForm',
                'click .cancel-button': 'clearSearch'
            },

            initialize: function() {
                this.$searchField = this.$el.find('.search-field');
                this.$searchButton = this.$el.find('.search-button');
                this.$cancelButton = this.$el.find('.cancel-button');
            },

            submitForm: function(event) {
                event.preventDefault();
                this.doSearch();
            },

            doSearch: function(term) {
                var trimmed;
                if (term) {
                    trimmed = term.trim();
                    this.$searchField.val(trimmed);
                } else {
                    trimmed = this.$searchField.val().trim();
                }
                if (trimmed) {
                    this.setActiveStyle();
                    this.trigger('search', trimmed);
                } else {
                    this.clearSearch();
                }
            },

            resetSearchForm: function() {
                this.$searchField.val('');
                this.setInitialStyle();
            },

            clearSearch: function() {
                this.resetSearchForm();
                this.trigger('clear');
            },

            setActiveStyle: function() {
                this.$searchField.addClass('is-active');
                this.$searchButton.hide();
                this.$cancelButton.show();
            },

            setInitialStyle: function() {
                this.$searchField.removeClass('is-active');
                this.$searchButton.show();
                this.$cancelButton.hide();
            }

        });
    });
}(define || RequireJS.define));
