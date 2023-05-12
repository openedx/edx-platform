(function(define) {
    define([
        'underscore',
        'backbone',
        'js/discovery/models/course_card',
        'js/discovery/models/facet_option'
    ], function(_, Backbone, CourseCard, FacetOption) {
        'use strict';

        return Backbone.Model.extend({
            url: '/search/course_discovery/',
            jqhxr: null,

            defaults: {
                totalCount: 0,
                latestCount: 0
            },

            initialize: function() {
                this.courseCards = new Backbone.Collection([], {model: CourseCard});
                this.facetOptions = new Backbone.Collection([], {model: FacetOption});
            },

            parse: function(response) {
                // eslint-disable-next-line no-var
                var courses = response.results || [];
                // eslint-disable-next-line no-var
                var facets = response.aggs || {};
                this.courseCards.add(_.pluck(courses, 'data'));

                this.set({
                    totalCount: response.total,
                    latestCount: courses.length
                });

                // eslint-disable-next-line no-var
                var options = this.facetOptions;
                _(facets).each(function(obj, key) {
                    _(obj.terms).each(function(count, term) {
                        options.add({
                            facet: key,
                            term: term,
                            count: count
                        }, {merge: true});
                    });
                });
            },

            reset: function() {
                this.set({
                    totalCount: 0,
                    latestCount: 0
                });
                this.courseCards.reset();
                this.facetOptions.reset();
            },

            latest: function() {
                return this.courseCards.last(this.get('latestCount'));
            }

        });
    });
// eslint-disable-next-line no-undef
}(define || RequireJS.define));
