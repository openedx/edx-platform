(function(define) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'moment',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!templates/student_profile/badge.underscore',
            'js/student_profile/views/share_modal_view'],
        function(gettext, $, _, Backbone, Moment, HtmlUtils, badgeTemplate, ShareModalView) {
            var BadgeView = Backbone.View.extend({
                attributes: {
                    class: 'badge-display'
                },
                template: HtmlUtils.template(badgeTemplate),
                events: {
                    'click .share-button': 'createModal'
                },

                initialize: function(options) {
                    this.options = _.extend({}, options);
                    this.context = _.extend(this.options.model.toJSON(), {
                        created: new Moment(this.options.model.toJSON().created),
                        ownProfile: options.ownProfile,
                        badgeMeta: options.badgeMeta
                    });
                },

                createModal: function() {
                    var modal = new ShareModalView({
                        model: new Backbone.Model(this.context),
                        shareButton: this.shareButton
                    });
                    modal.$el.hide();
                    modal.render();
                    $('body').append(modal.$el);
                    modal.$el.fadeIn('short', 'swing', _.bind(modal.ready, modal));
                },

                render: function() {
                    HtmlUtils.setHtml(this.$el, this.template(this.context));
                    this.shareButton = this.$el.find('.share-button');
                    return this;
                }
            });

            return BadgeView;
        });
}).call(this, define || RequireJS.define);
