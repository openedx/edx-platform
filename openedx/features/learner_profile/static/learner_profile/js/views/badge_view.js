(function(define) {
    'use strict';

    define(
        [
            'gettext', 'jquery', 'backbone', 'moment',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!learner_profile/templates/badge.underscore',
            'learner_profile/js/views/share_modal_view'
        ],
        function(gettext, $, Backbone, Moment, HtmlUtils, badgeTemplate, ShareModalView) {
            var BadgeView = Backbone.View.extend({
                initialize: function(options) {
                    this.options = Object.assign({}, options);
                    this.context = Object.assign(this.options.model.toJSON(), {
                        created: new Moment(this.options.model.toJSON().created),
                        ownProfile: options.ownProfile,
                        badgeMeta: options.badgeMeta
                    });
                },
                attributes: {
                    class: 'badge-display'
                },
                template: HtmlUtils.template(badgeTemplate),
                events: {
                    'click .share-button': 'createModal'
                },
                createModal: function() {
                    var modal = new ShareModalView({
                        model: new Backbone.Model(this.context),
                        shareButton: this.shareButton
                    });
                    modal.$el.hide();
                    modal.render();
                    $('body').append(modal.$el);
                    modal.$el.fadeIn('short', 'swing', modal.ready.bind(modal));
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
