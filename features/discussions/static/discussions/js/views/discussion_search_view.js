(function(define) {
    'use strict';

    define([
        'underscore',
        'backbone',
        'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/constants',
        'text!discussion/templates/search.underscore'
    ],
    function(_, Backbone, HtmlUtils, constants, searchTemplate) {
        /*
         * TODO: Much of the actual search functionality still takes place in discussion_thread_list_view.js
         * Because of how it's structured there, extracting it is a massive task. Significant refactoring is needed
         * in order to clean up that file and make it possible to break its logic into files like this one.
         */
        var searchView = Backbone.View.extend({
            initialize: function(options) {
                _.extend(this, _.pick(options, ['discussionBoardView']));

                this.template = HtmlUtils.template(searchTemplate);
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },
            render: function() {
                HtmlUtils.setHtml(this.$el, this.template());
                return this;
            }
        });

        return searchView;
    });
}).call(this, define || RequireJS.define);
