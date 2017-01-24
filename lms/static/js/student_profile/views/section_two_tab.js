(function(define, undefined) {
    'use strict';
    define([
        'gettext', 'jquery', 'underscore', 'backbone', 'text!templates/student_profile/section_two.underscore'],
        function(gettext, $, _, Backbone, sectionTwoTemplate) {
            var SectionTwoTab = Backbone.View.extend({
                attributes: {
                    'class': 'wrapper-profile-section-two'
                },
                template: _.template(sectionTwoTemplate),
                initialize: function(options) {
                    this.options = _.extend({}, options);
                },
                render: function() {
                    var self = this;
                    var showFullProfile = this.options.showFullProfile();
                    this.$el.html(this.template({
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
