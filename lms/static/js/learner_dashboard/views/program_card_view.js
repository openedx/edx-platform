;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/program_card.underscore',
            'picturefill'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             programCardTpl,
             picturefill
         ) {
            return Backbone.View.extend({
                className: 'program-card',
                tpl: _.template(programCardTpl),
                initialize: function() {
                    this.render();
                },
                render: function() {
                    var templated = this.tpl(this.model.toJSON());
                    this.$el.html(templated);
                    this.postRender();
                },
                postRender: function() {
                    if(navigator.userAgent.indexOf('MSIE') !== -1 ||
                        navigator.appVersion.indexOf('Trident/') > 0){
                        /* Microsoft Internet Explorer detected in. */
                        window.setTimeout( function() {
                            this.reLoadBannerImage();
                        }.bind(this), 100);
                    }
                },
                // Defer loading the rest of the page to limit FOUC
                reLoadBannerImage: function() {
                    var $img = this.$('.program_card .banner-image'),
                        imgSrcAttr = $img ? $img.attr('src') : {};
                    
                    if (!imgSrcAttr || imgSrcAttr.length < 0) {
                        try{
                            this.reEvaluatePicture();
                        }catch(err){
                            //Swallow the error here
                        }
                    }
                },

                reEvaluatePicture: function(){
                    picturefill({
                        reevaluate: true
                    });
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
