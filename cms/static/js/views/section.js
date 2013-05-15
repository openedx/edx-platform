CMS.Views.SectionShow = Backbone.View.extend({
    template: _.template('<span data-tooltip="Edit this section\'s name" class="section-name-span"><%= name %></span>'),
    render: function() {
        this.$el.html(this.template(this.model.attributes));
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
    template: _.template($("#section-name-edit-tpl").text()),
    render: function() {
        this.$el.html(this.template(this.model.attributes));
        this.delegateEvents();
        return this;
    },
    initialize: function() {
        this.listenTo(this.model, "invalid", this.showErrorMessage);
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
    showErrorMessage: function(model, error, options) {
        var that = this;
        var msg = new CMS.Models.ErrorMessage({
            title: "Validation Error",
            message: error,
            actions: {
                primary: {
                    text: "Dismiss",
                    click: function(view) {
                        view.hide();
                        that.$("input[type=text]").focus();
                    }
                }
            }
        });
        new CMS.Views.Prompt({model: msg});
    }
});
