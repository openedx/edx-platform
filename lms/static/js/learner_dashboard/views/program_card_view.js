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
                         'aria-labelledby': 'program-' + this.model.get('id'),
                         'role': 'group'
                     };
                 },

                 tpl: _.template(programCardTpl),

                 initialize: function(data) {
                     this.progressCollection = data.context.progressCollection;
                     if (this.progressCollection) {
                         this.progressModel = this.progressCollection.findWhere({
                             id: this.model.get('id')
                         });
                     }
                     this.render();
                 },

                 render: function() {
                     var orgList = _.map(this.model.get('organizations'), function(org) {
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
                    // Add describedby to parent only if progess is present
                     if (this.progressModel) {
                         this.$el.attr('aria-describedby', 'status-' + this.model.get('id'));
                     }

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
                         progress.total = {
                             completed: progress.completed.length,
                             in_progress: progress.in_progress.length,
                             not_started: progress.not_started.length
                         };

                         progress.total.courses = progress.total.completed +
                                                 progress.total.in_progress +
                                                 progress.total.not_started;

                         progress.percentage = {
                             completed: this.getWidth(progress.total.completed, progress.total.courses),
                             in_progress: this.getWidth(progress.total.in_progress, progress.total.courses)
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
