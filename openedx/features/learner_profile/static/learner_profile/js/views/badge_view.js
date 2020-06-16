(function(define) {
    'use strict';

    define(
        [
            'gettext', 'jquery', 'underscore', 'backbone', 'moment',
            'text!learner_profile/templates/badge.underscore',
            'learner_profile/js/views/share_modal_view',
            'edx-ui-toolkit/js/utils/html-utils'
        ],
        function(gettext, $, _, Backbone, Moment, badgeTemplate, ShareModalView, HtmlUtils) {
            var BadgeView = Backbone.View.extend({
                initialize: function(options) {
                    this.options = _.extend({}, options);
                    this.context = _.extend(this.options.model.toJSON(), {
                        created: new Moment(this.options.model.toJSON().created),
                        ownProfile: options.ownProfile,
                        badgeMeta: options.badgeMeta
                    });
                },
                attributes: {
                    class: 'badge-display'
                },
                template: _.template(badgeTemplate),
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
                    modal.$el.fadeIn('short', 'swing', _.bind(modal.ready, modal));
                },
                render: function() {
                    this.$el.html(HtmlUtils.HTML(this.template(this.context)).toString());
                    this.shareButton = this.$el.find('.share-button');
                    return this;
                }
            });

            return BadgeView;
        });
}).call(this, define || RequireJS.define);
