(function(define) {
    'use strict';

    define(
        [
            'gettext', 'jquery', 'backbone',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!learner_profile/templates/section_two.underscore'
        ],
        function(gettext, $, Backbone, HtmlUtils, sectionTwoTemplate) {
            var SectionTwoTab = Backbone.View.extend({
                attributes: {
                    class: 'wrapper-profile-section-two'
                },
                template: HtmlUtils.template(sectionTwoTemplate),
                initialize: function(options) {
                    this.options = Object.assign({}, options);
                },
                render: function() {
                    var self = this;
                    var showFullProfile = this.options.showFullProfile();
                    HtmlUtils.setHtml(this.$el, this.template({
                        ownProfile: self.options.ownProfile,
                        showFullProfile: showFullProfile
                    }));
                    if (showFullProfile) {
                        this.options.viewList.forEach(function(fieldView) {
                            self.$el.find('.field-container').append(fieldView.render().el);
                        });
                    }
                    return this;
                }
            });

            return SectionTwoTab;
        });
}).call(this, define || RequireJS.define);
