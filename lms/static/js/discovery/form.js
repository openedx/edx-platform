;(function (define) {

define(['jquery', 'backbone'], function ($, Backbone) {
   'use strict';

    return Backbone.View.extend({

        el: '#discovery-form',
        events: {
            'submit form': 'submitForm',
        },

        initialize: function () {
            this.$searchField = this.$el.find('input');
            this.$searchButton = this.$el.find('button');
            this.$message = this.$el.find('#discovery-message');
            this.$loadingIndicator = this.$el.find('#loading-indicator');
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
            this.trigger('search', trimmed);
            this.$message.empty();
        },

        clearSearch: function () {
            this.$searchField.val('');
        },

        showLoadingIndicator: function () {
            this.$loadingIndicator.removeClass('hidden');
        },

        hideLoadingIndicator: function () {
            this.$loadingIndicator.addClass('hidden');
        },

        showNotFoundMessage: function (term) {
            var msg = term != '' ?
                interpolate(gettext('We couldn\'t find any results for "%s."'), [term]) :
                gettext('We couldn\'t find any results.');
            this.$message.html(msg);
        },

        showErrorMessage: function () {
            this.$message.html(gettext('There was an error, try searching again.'));
        }

    });

});

})(define || RequireJS.define);
