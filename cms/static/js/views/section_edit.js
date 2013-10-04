define(["backbone", "underscore", "js/views/feedback_prompt", "js/views/section_show", "require"], function(Backbone, _, PromptView, SectionShowView, require) {
    var SectionEdit = Backbone.View.extend({
        render: function() {
            var attrs = {
                name: this.model.escape('name')
            };
            this.$el.html(this.template(attrs));
            this.delegateEvents();
            return this;
        },
        initialize: function() {
            this.template = _.template($("#section-name-edit-tpl").text());
            this.listenTo(this.model, "invalid", this.showInvalidMessage);
            this.render();
        },
        events: {
            "click .save-button": "saveName",
            "submit": "saveName",
            "click .cancel-button": "switchToShowView"
        },
        saveName: function(e) {
            if (e) { e.preventDefault(); }
            var name = this.$("input[type=text]").val();
            var that = this;
            this.model.save("name", name, {
                success: function() {
                    analytics.track('Edited Section Name', {
                        'course': course_location_analytics,
                        'display_name': that.model.get('name'),
                        'id': that.model.get('id')
                    });
                    that.switchToShowView();
                }
            });
        },
        switchToShowView: function() {
            if(!this.showView) {
                SectionShowView = require('js/views/section_show');
                this.showView = new SectionShowView({
                    model: this.model, el: this.el, editView: this});
            }
            this.undelegateEvents();
            this.stopListening();
            this.showView.render();
        },
        showInvalidMessage: function(model, error, options) {
            model.set("name", model.previous("name"));
            var that = this;
            var prompt = new PromptView.Error({
                title: gettext("Your change could not be saved"),
                message: error,
                actions: {
                    primary: {
                        text: gettext("Return and resolve this issue"),
                        click: function(view) {
                            view.hide();
                            that.$("input[type=text]").focus();
                        }
                    }
                }
            });
            prompt.show();
        }
    });
    return SectionEdit;
});
