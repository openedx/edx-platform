CMS.Views.SectionShow = Backbone.View.extend({
    template: _.template('<span data-tooltip="<%= gettext("Edit this section\'s name") %>" class="section-name-span"><%= name %></span>'),
    render: function() {
        var attrs = {
            name: this.model.escape('name')
        };
        this.$el.html(this.template(attrs));
        this.delegateEvents();
        return this;
    },
    events: {
        "click": "switchToEditView"
    },
    switchToEditView: function() {
        if(!this.editView) {
            this.editView = new CMS.Views.SectionEdit({
                model: this.model, el: this.el, showView: this});
        }
        this.undelegateEvents();
        this.editView.render();
    }
});

CMS.Views.SectionEdit = Backbone.View.extend({
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
            this.showView = new CMS.Views.SectionShow({
                model: this.model, el: this.el, editView: this});
        }
        this.undelegateEvents();
        this.stopListening();
        this.showView.render();
    },
    showInvalidMessage: function(model, error, options) {
        model.set("name", model.previous("name"));
        var that = this;
        var prompt = new CMS.Views.Prompt.Error({
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
