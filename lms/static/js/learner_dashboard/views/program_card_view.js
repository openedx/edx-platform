(function(define) {
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

                 attributes: function() {
                     return {
                         'aria-labelledby': 'program-' + this.model.get('uuid'),
                         'role': 'group'
                     };
                 },

                 tpl: _.template(programCardTpl),

                 initialize: function(data) {
                     this.progressCollection = data.context.progressCollection;
                     if (this.progressCollection) {
                         this.progressModel = this.progressCollection.findWhere({
                             uuid: this.model.get('uuid')
                         });
                     }
                     this.render();
                 },

                 render: function() {
                     var orgList = _.map(this.model.get('authoring_organizations'), function(org) {
                             return gettext(org.key);
                         }),
                         data = $.extend(
                            this.model.toJSON(),
                            this.getProgramProgress(),
                            {orgList: orgList.join(' ')}
                        );

                     this.$el.html(this.tpl(data));
                     this.postRender();
                 },

                 postRender: function() {
                     if (navigator.userAgent.indexOf('MSIE') !== -1 ||
                        navigator.appVersion.indexOf('Trident/') > 0) {
                        /* Microsoft Internet Explorer detected in. */
                         window.setTimeout(function() {
                             this.reLoadBannerImage();
                         }.bind(this), 100);
                     }
                 },

                // Calculate counts for progress and percentages for styling
                 getProgramProgress: function() {
                     var progress = this.progressModel ? this.progressModel.toJSON() : false;

                     if (progress) {

                         progress.total = progress.completed +
                                          progress.in_progress +
                                          progress.not_started;

                         progress.percentage = {
                             completed: this.getWidth(progress.completed, progress.total),
                             in_progress: this.getWidth(progress.in_progress, progress.total)
                         };
                     }

                     return {
                         progress: progress
                     };
                 },

                 getWidth: function(val, total) {
                     var int = (val / total) * 100;

                     return int + '%';
                 },

                // Defer loading the rest of the page to limit FOUC
                 reLoadBannerImage: function() {
                     var $img = this.$('.program_card .banner-image'),
                         imgSrcAttr = $img ? $img.attr('src') : {};

                     if (!imgSrcAttr || imgSrcAttr.length < 0) {
                         try {
                             this.reEvaluatePicture();
                         } catch (err) {
                            // Swallow the error here
                         }
                     }
                 },

                 reEvaluatePicture: function() {
                     picturefill({
                         reevaluate: true
                     });
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
