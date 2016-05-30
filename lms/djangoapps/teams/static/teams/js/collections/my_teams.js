;(function (define) {
    'use strict';
    define(['teams/js/collections/team'], function (TeamCollection) {
        var MyTeamsCollection = TeamCollection.extend({
            queryParams: {
                username: function () {
                    return this.options.username;
                },
                text_search: function () {
                    return this.searchString || '';
                },
                totalPages: null,
                totalRecords: null
            },

            constructor: function (teams, options) {
                TeamCollection.prototype.constructor.call(this, teams, options);
                delete this.queryParams.topic_id;
            }
        });
        return MyTeamsCollection;
    });
}).call(this, define || RequireJS.define);
