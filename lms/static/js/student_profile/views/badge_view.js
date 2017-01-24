(function(define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'moment',
            'text!templates/student_profile/badge.underscore',
            'js/student_profile/views/share_modal_view'],
        function(gettext, $, _, Backbone, Moment, badgeTemplate, ShareModalView) {
            var BadgeView = Backbone.View.extend({
                initialize: function(options) {
                    this.options = _.extend({}, options);
                    this.context = _.extend(this.options.model.toJSON(), {
                        'created': new Moment(this.options.model.toJSON().created),
                        'ownProfile': options.ownProfile,
                        'badgeMeta': options.badgeMeta
                    });
                },
                attributes: {
                    'class': 'badge-display'
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
                    this.$el.html(this.template(this.context));
                    this.shareButton = this.$el.find('.share-button');
                    return this;
                }
            });

            return BadgeView;
        });
}).call(this, define || RequireJS.define);
