;(function (define) {

define([
    'backbone',
    'js/revisions/models/revision'
], function (Backbone, Revision) {
    'use strict';

    return Backbone.Collection.extend({

        model: Revision,
        url: '/api/revisions/',
        fetchXhr: null,

        fetchRevisions: function () {
            this.fetchXhr && this.fetchXhr.abort();
            this.resetState();
            this.fetchXhr = this.fetch({
                data: {},
                type: 'GET',
                success: function (self, xhr) {
                    self.trigger('revisions_loaded');
                },
                error: function (self, xhr) {
                    self.trigger('error');
                }
            });
        },

        resetState: function () {
            // empty the entire collection
            this.reset();
        },

    });

});


})(define || RequireJS.define);
