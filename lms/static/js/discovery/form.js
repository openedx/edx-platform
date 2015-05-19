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
            this.trigger('search', $.trim(term));
            this.$message.empty();
        },

        clearSearch: function () {
            this.$message.empty();
            this.$searchField.val('');
        },

        showLoadingIndicator: function () {
            this.$message.empty();
            this.$loadingIndicator.removeClass('hidden');
        },

        hideLoadingIndicator: function () {
            this.$loadingIndicator.addClass('hidden');
        },

        showNotFoundMessage: function (term) {
            var msg = interpolate(
                gettext('We couldn\'t find any results for "%s".'),
                [_.escape(term)]
            );
            this.$message.html(msg);
        },

        showErrorMessage: function () {
            this.$message.html(gettext('There was an error, try searching again.'));
        }

    });

});

})(define || RequireJS.define);
