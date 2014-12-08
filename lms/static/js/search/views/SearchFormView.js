var edx = edx || {};

(function ($, Backbone) {
   'use strict'

    edx.search = edx.search || {};

    edx.search.SearchFormView = Backbone.View.extend({
        el: '#couserware-search',
        events: {
            'submit form': 'performSearch',
        },

        performSearch: function () {
            var searchTerm = this.$el.find('[type="text"]').val();
            this.collection.performSearch(searchTerm);
            this.$el.find('.search-button').hide();
            this.$el.find('.cancel-button').show();
            // prevent reload
            return false;
        },

        initialize: function (options) {
            this.collection = options.collection || {};
        }

    });

})(jQuery, Backbone);
