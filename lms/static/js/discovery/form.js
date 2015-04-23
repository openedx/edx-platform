;(function (define) {

define(['jquery', 'backbone'], function ($, Backbone) {
   'use strict';

    return Backbone.View.extend({

        el: '#discovery-form',
        events: {
            'submit form': 'submitForm',
            'click #discovery-clear': 'clearSearch',
        },

        initialize: function () {
            this.$searchField = this.$el.find('input');
            this.$searchButton = this.$el.find('button');
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
                this.trigger('search', trimmed);
            }
        },

        showClearAllButton: function () {
            this.$el.find('#discovery-clear').removeClass('hidden');
        },

        hideClearAllButton: function() {
            this.$el.find('#discovery-clear').addClass('hidden');
        },

        clearSearch: function () {
            this.$searchField.val('');
            this.trigger('clear');
            return false;
        }

    });

});

})(define || RequireJS.define);
