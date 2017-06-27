(function(define) {
    'use strict';

    define(['jquery', 'backbone'], function($, Backbone) {
        return Backbone.View.extend({

            el: '',
            events: {
                'submit .search-form': 'submitForm',
                'click .cancel-button': 'clearSearch'
            },

            initialize: function(options) {
                this.$searchField = this.$el.find('.search-field');
                this.$searchButton = this.$el.find('.search-button');
                this.$cancelButton = this.$el.find('.cancel-button');
                this.supportsActive = options.supportsActive === undefined ? true : options.supportsActive;
            },

            submitForm: function(event) {
                event.preventDefault();
                this.doSearch();
            },

            doSearch: function(term) {
                var trimmedTerm;
                if (term) {
                    trimmedTerm = term.trim();
                    this.$searchField.val(trimmedTerm);
                } else {
                    trimmedTerm = this.$searchField.val().trim();
                }
                if (trimmedTerm) {
                    this.setActiveStyle();
                    this.trigger('search', trimmedTerm);
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
                if (this.supportsActive) {
                    this.$searchField.addClass('is-active');
                    this.$searchButton.hide();
                    this.$cancelButton.show();
                }
            },

            setInitialStyle: function() {
                if (this.supportsActive) {
                    this.$searchField.removeClass('is-active');
                    this.$searchButton.show();
                    this.$cancelButton.hide();
                }
            }
        });
    });
}(define || RequireJS.define));
