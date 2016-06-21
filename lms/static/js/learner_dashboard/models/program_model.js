/**
 * Model for Course Programs.
 */
(function (define) {
    'use strict';
    define([
            'backbone'
        ], 
        function (Backbone) {
        return Backbone.Model.extend({
            initialize: function(data) {
                if (data){
                    this.set({
                        name: data.name,
                        type: data.display_category + ' Program',
                        subtitle: data.subtitle,
                        organizations: data.organizations,
                        detailUrl: data.detail_url,
                        smallBannerUrl: data.banner_image_urls.w348h116,
                        mediumBannerUrl: data.banner_image_urls.w435h145,
                        largeBannerUrl: data.banner_image_urls.w726h242,
                        breakpoints: {
                            max: {
                                tiny: '320px',
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
