/**
 * Model for Course Programs.
 */
(function(define) {
    'use strict';
    define([
        'backbone'
    ],
        function(Backbone) {
            return Backbone.Model.extend({
                initialize: function(data) {
                    if (data) {
                        this.set({
                            title: data.title,
                            type: data.type,
                            subtitle: data.subtitle,
                            authoring_organizations: data.authoring_organizations,
                            detailUrl: data.detail_url,
                            xsmallBannerUrl: data.banner_image['x-small'].url,
                            smallBannerUrl: data.banner_image.small.url,
                            mediumBannerUrl: data.banner_image.medium.url,
                            breakpoints: {
                                max: {
                                    xsmall: '320px',
                                    small: '540px',
                                    medium: '768px',
                                    large: '979px'
                                }
                            }
                        });
                    }
                }
            });
        });
}).call(this, define || RequireJS.define);
