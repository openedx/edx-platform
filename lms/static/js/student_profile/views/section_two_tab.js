(function(define) {
    'use strict';
    define([
            'gettext', 'jquery', 'underscore', 'backbone',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!templates/student_profile/section_two.underscore'],
        function(gettext, $, _, Backbone, HtmlUtils, sectionTwoTemplate) {

            var SectionTwoTab = Backbone.View.extend({
                attributes: {
                    'class': 'wrapper-profile-section-two'
                },
                template: HtmlUtils.template(sectionTwoTemplate),

                initialize: function(options) {
                    this.options = _.extend({}, options);
                },

                render: function() {
                    var self = this,
                        showFullProfile = this.options.showFullProfile();
                    HtmlUtils.setHtml(this.$el, this.template({
                        ownProfile: self.options.ownProfile,
                        showFullProfile: showFullProfile
                    }));
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
