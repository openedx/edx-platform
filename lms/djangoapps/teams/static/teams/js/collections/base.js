/* globals _ */
(function(define) {
    'use strict';
    define(['edx-ui-toolkit/js/pagination/paging-collection'],
        function(PagingCollection) {
            var BaseCollection = PagingCollection.extend({
                constructor: function(models, options) {
                    this.options = options;
                    this.url = options.url;
                    if (options.perPage) {
                        this.state.pageSize = options.perPage;
                    }

                    this.course_id = options.course_id;
                    this.teamEvents = options.teamEvents;
                    this.teamEvents.bind('teams:update', this.onUpdate, this);

                    this.queryParams = _.extend({}, BaseCollection.prototype.queryParams, this.queryParams);
                    PagingCollection.prototype.constructor.call(this, models, options);
                },

                parse: function(response, options) {
                    if (!response) {
                        response = {}; // eslint-disable-line no-param-reassign
                    }

                    if (!response.results) {
                        response.results = []; // eslint-disable-line no-param-reassign
                    }

                    return PagingCollection.prototype.parse.call(this, response, options);
                },

                onUpdate: function(event) { // eslint-disable-line no-unused-vars
                    // Mark the collection as stale so that it knows to refresh when needed.
                    this.isStale = true;
                },

                // TODO: These changes has been added to backbone.paginator
                // remove when backbone.paginator gets a new release
                sync: function(method, model, options) {
                    // do not send total pages and total records in request
                    var params;
                    if (method === 'read') {
                        params = _.values(_.pick(this.queryParams, ['totalPages', 'totalRecords']));
                        _.each(params, function(param) {
                            delete options.data[param]; // eslint-disable-line no-param-reassign
                        });
                    }

                    return PagingCollection.prototype.sync(method, model, options);
                }
            });
            return BaseCollection;
        });
}).call(this, define || RequireJS.define);
