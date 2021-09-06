(function(define) {
    'use strict';

    define(
        [
            'gettext', 'jquery', 'underscore', 'backbone', 'text!learner_profile/templates/section_two.underscore',
            'edx-ui-toolkit/js/utils/html-utils'
        ],
        function(gettext, $, _, Backbone, sectionTwoTemplate, HtmlUtils) {
            var SectionTwoTab = Backbone.View.extend({
                attributes: {
                    class: 'wrapper-profile-section-two'
                },
                template: _.template(sectionTwoTemplate),
                initialize: function(options) {
                    this.options = _.extend({}, options);
                },
                render: function() {
                    var self = this;
                    var showFullProfile = this.options.showFullProfile();
                    this.$el.html(HtmlUtils.HTML(this.template({ownProfile: self.options.ownProfile, showFullProfile: showFullProfile})).toString()); // eslint-disable-line max-len
                    if (showFullProfile) {
                        _.each(this.options.viewList, function(fieldView) {
                            self.$el.find('.field-container').append(fieldView.render().el);
                        });
                    }
                    return this;
                }
            });

            return SectionTwoTab;
        });
}).call(this, define || RequireJS.define);
